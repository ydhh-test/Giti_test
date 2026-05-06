# -*- coding: utf-8 -*-

"""
纵向细沟 & 纵向钢片检测模块（Rule 11）

检测模型生成的小图（128×128）中纵向细线条（纵向细沟 / 纵向钢片）的位置和数量。

支持类型：
- ``center`` 小图 → 对应 RIB2/3/4，允许 0-2 条纵向线条
- ``side``   小图 → 对应 RIB1/5，  允许 0-1 条纵向线条

宽度标准：名义宽度约 4px（0.34mm × 11.81px/mm），容差 ±50%（约 2~6 px）。
         宽度判断采用"逐行水平跨度均值"而非 bounding-box 宽度，对斜线更准确。
长度标准：宽度达标后，连续线段纵向长度超过图片宽度的 1/5 即可判定为纵沟。
角度标准：相邻行中心列偏移经 7 点滑动均值平滑后，偏离竖直方向不超过 30° 的
         连续子段计为一条纵沟。超出角度的行为"切割点"，令竖线与斜线各自独立计数。
         （此设计解决了"竖线通过斜线连接"导致整段被误判的问题）
分离线段分别计数：同一列带中的多个分离连续段，按多条纵沟分别统计。
左右边缘排除：默认跳过图像左右各 10% 的列，以避免主沟残留被误检。

评分规则：
- 纵向线条数量在允许范围内 → 4 分（满分）
- 超出允许范围             → 0 分
"""

import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

import logging
from src.common.exceptions import InputDataError, RuntimeProcessError

logger = logging.getLogger(__name__)

# ============================================================
# 模块级默认常量（不依赖 configs 层，由调用方参数覆盖）
# ============================================================

# center 小图 → RIB2/3/4；side 小图 → RIB1/5
_RIB_LABEL: dict = {"center": "RIB2/3/4", "side": "RIB1/5"}
# 各类型允许的最大纵向线条数量
_MAX_COUNT: dict = {"center": 2, "side": 1}
# Rule 11 算法层最大分值（仅供内部调试图标注使用；正式评分由 rules/scores/rule_11.py 负责）
_MAX_SCORE: int = 4


# ============================================================
# 主函数
# ============================================================

def detect_longitudinal_grooves(
    image: np.ndarray,
    image_type: str,
    groove_width_mm: float = 0.34,
    pixel_per_mm: float = 11.81,
    min_width_offset_px: int = 1,
    edge_margin_ratio: float = 0.10,
    min_segment_length_ratio: float = 0.12,
    max_angle_deg: float = 30.0,
) -> Tuple[float, Dict[str, Any]]:
    """
    检测纵向细线条（纵向细沟 / 纵向钢片）的位置和数量。

    Parameters
    ----------
    image : np.ndarray
        BGR 图像数组，期望尺寸 (128, 128, 3)。
    image_type : str
        小图类型，``"center"``（对应 RIB2/3/4）或 ``"side"``（对应 RIB1/5）。
    groove_width_mm : float
        纵向线条的名义宽度（mm）。默认 0.34mm（约 4px @ 11.81px/mm）。
    pixel_per_mm : float
        图像像素密度（px/mm）。客户标准默认 11.81。
    min_width_offset_px : int
        宽度下限偏移量（像素）。最小可接受宽度 = ``round(nominal_px) - min_width_offset_px``。
        无上限约束——任何宽度 ≥ 下限的线条均被认定有效。
        默认 1，即 nominal=4px 时下限为 3px。
        宽度计算方式：对连通域逐行计算水平跨度，取各行均值。
    edge_margin_ratio : float
        左右边缘排除比例（相对图像宽度）。左右各排除 ``img_w × edge_margin_ratio``
        列，防止将主沟截取残留误检为纵向细沟。默认 0.10（约 13 px @ 128px 图像）。
    min_segment_length_ratio : float
        连续线段最小长度比例。宽度达标后，若线段纵向长度超过
        ``img_w × min_segment_length_ratio``，则计为 1 条纵沟。默认 0.12。
    max_angle_deg : float
        相邻行允许的最大偏转角度（度）。超过此值则在该处将连通域切割为子段，
        仅保留近竖直子段参与计数。通过 7 点滑动均值消除像素量化误差。
        默认 30.0°。

    Returns
    -------
    details : dict
        成功时包含以下键：

        - ``rib_type``        (*str*)             ：RIB 类型，``"RIB2/3/4"`` 或 ``"RIB1/5"``
        - ``groove_count``    (*int*)             ：检测到的纵向线条数量
        - ``groove_positions``(*list[float]*)     ：各线条中心 X 坐标（升序，像素）
        - ``groove_widths``   (*list[float]*)     ：各线条宽度（像素，与 positions 对应）
        - ``is_valid``        (*bool*)            ：数量是否在允许范围内（结构性，不含评分）
        - ``line_mask``       (*ndarray*)         ：纵向线条掩码（白色=检测到的线条）
        - ``debug_image``     (*ndarray*)         ：BGR 标注调试图

        失败时仅包含：

        - ``err_msg``    (*str*) ：错误描述
        - ``error_type`` (*str*) ：异常类型名称
    """
    try:
        logger.debug("开始纵向线条检测，image_type=%s", image_type)

        # ── 输入验证 ──────────────────────────────────────────────────
        if image is None:
            raise InputDataError("image", "value", "must not be None")

        if image.ndim != 3 or image.shape[2] != 3:
            raise InputDataError("image", "shape", "expected (H, W, 3)", image.shape)

        image_type = image_type.strip().lower()
        if image_type not in _RIB_LABEL:
            raise InputDataError("image_type", "value", "must be 'center' or 'side'", image_type)

        # ── 参数准备 ───────────────────────────────────────────────────
        nominal_px = groove_width_mm * pixel_per_mm
        min_w_px          = max(1, int(round(nominal_px)) - min_width_offset_px)
        narrow_cluster_px = max(min_w_px + 1, int(round(nominal_px * 2)))  # 仅用于行内窄簇筛选
        rib_type   = _RIB_LABEL[image_type]
        max_count  = _MAX_COUNT[image_type]
        img_h, img_w = image.shape[:2]

        edge_margin_px = max(0, int(img_w * edge_margin_ratio))
        min_segment_len_px = max(1, int(np.ceil(img_w * min_segment_length_ratio)))
        logger.debug(
            "rib_type=%s, nominal_px=%.1f, min_w_px=%dpx（无上限）, min_segment_len_px=%d, max_count=%d, edge_margin_px=%d, max_angle_deg=%.0f",
            rib_type, nominal_px, min_w_px, min_segment_len_px, max_count, edge_margin_px, max_angle_deg,
        )

        # ── Step 1: 灰度转换 + 高斯模糊降噪 ─────────────────────────
        gray    = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # ── Step 2: 自适应二值化（暗色线条 → 白色前景）──────────────
        # blockSize=31 适配 128px 小图的局部对比度窗口
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=31, C=5,
        )

        # ── Step 3: 连通域分析识别纵向线条 ──────────────────────────
        positions, count, line_mask, widths = _analyze_vertical_lines(
            binary, min_w_px, narrow_cluster_px, img_h, edge_margin_px,
            min_segment_len_px, max_angle_deg,
        )
        logger.debug("纵向线条数量=%d, 位置=%s", count, positions)

        # ── Step 4: 合规判定（结构性，不含评分；正式评分由 rules/scores/rule_11 负责）
        is_valid = count <= max_count

        # ── Step 5: 生成调试标注图 ────────────────────────────────────
        debug_image = _draw_debug_image(
            image, line_mask, positions, widths,
            rib_type, count, max_count, is_valid,
        )

        details: Dict[str, Any] = {
            "rib_type":         rib_type,
            "groove_count":     count,
            "groove_positions": positions,
            "groove_widths":    widths,
            "is_valid":         is_valid,
            "line_mask":        line_mask,
            "debug_image":      debug_image,
        }
        logger.debug("纵向线条检测完成，count=%d, is_valid=%s", count, is_valid)
        return details

    except Exception as exc:
        err_msg    = str(exc)
        error_type = type(exc).__name__
        logger.error("纵向线条检测失败：%s", err_msg)
        return {"err_msg": err_msg, "error_type": error_type}


# ============================================================
# 内部辅助函数
# ============================================================

def _bridge_small_vertical_gaps(binary: np.ndarray, max_gap_px: int = 4) -> np.ndarray:
    """
    用形态学闭运算桥接纵向小间隙，避免交替明暗纹理把一条线段切碎。

    仅桥接小于等于 ``max_gap_px`` 的垂直空洞，大间隙仍保留为分离线段，
    以便后续按多条连续段分别计数。
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max_gap_px + 1))
    return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)


def _split_row_data_by_angle(
    row_data: List[Tuple[int, float, float]],
    max_angle_deg: float,
    smooth_half_window: int = 3,
) -> List[List[Tuple[int, float, float]]]:
    """
    将逐行中心数据按"局部坡度"切割为若干「近竖直子段」。

    算法：
    1. 对 center_x 序列做宽度为 ``2*smooth_half_window+1`` 的均匀滑动均值，
       消除整像素量化引起的锯齿跳变（默认 7 点均值）。
    2. 比较相邻行的平滑后 center_x 差值：
       若 ``|Δcx| / row_gap > tan(max_angle_deg)``，则在此处插入切割点。
    3. 每段独立返回，供后续高度/宽度过滤使用。

    此设计使"竖线 + 斜线"型连通域在角度突变处被正确拆分，
    竖直子段得以独立保留，斜线部分被排除在外。

    Parameters
    ----------
    row_data : list of (row, center_x, row_width)
        按行升序排列的连通域逐行数据。
    max_angle_deg : float
        允许的最大偏竖直角度（度）。
    smooth_half_window : int
        滑动均值半径（默认 3 → 7 点均值），用于消除像素量化误差。

    Returns
    -------
    list of sub-segment row_data lists（每段按行升序）
    """
    if not row_data:
        return []
    if len(row_data) == 1:
        return [row_data]

    n   = len(row_data)
    cxs = np.array([rd[1] for rd in row_data], dtype=np.float64)

    # 滑动均值平滑（边界处自动缩短窗口）
    smooth_cxs = np.array([
        cxs[max(0, i - smooth_half_window) : min(n, i + smooth_half_window + 1)].mean()
        for i in range(n)
    ])

    tan_max = float(np.tan(np.radians(max_angle_deg)))

    segments: List[List[Tuple[int, float, float]]] = []
    seg_start = 0

    for i in range(1, n):
        prev_row = row_data[i - 1][0]
        curr_row = row_data[i][0]
        row_gap  = max(1, curr_row - prev_row)
        dx       = abs(smooth_cxs[i] - smooth_cxs[i - 1])

        if dx > tan_max * row_gap:
            segments.append(row_data[seg_start:i])
            seg_start = i

    segments.append(row_data[seg_start:])
    return [s for s in segments if s]


def _analyze_vertical_lines(
    binary: np.ndarray,
    min_w_px: int,
    narrow_cluster_px: int,
    img_h: int,
    edge_margin_px: int = 0,
    min_segment_len_px: int = 1,
    max_angle_deg: float = 30.0,
) -> Tuple[List[float], int, np.ndarray, List[float]]:
    """
    通过连通域分析识别纵向线条（支持轻微倾斜，可从混合型连通域中提取竖直子段）。

    核心流程
    --------
    对每个连通域按行扫描，提取逐行中心 x 和宽度，然后调用
    ``_split_row_data_by_angle`` 在角度突变处切割，把"竖线 + 斜线"型
    连通域拆分为若干「近竖直子段」。每个子段独立判定：

    1. 子段实际高度（末行 - 首行 + 1）≥ ``min_segment_len_px``
    2. 逐行水平跨度均值 ≥ ``min_w_px``（无上限约束）

    同时满足以上条件的子段计为 1 条纵沟。

    Parameters
    ----------
    binary : np.ndarray
        自适应二值化图像（暗色线条 = 白色前景）。
    min_w_px : int
        纵向线条最小宽度（像素，逐行均值）。
    narrow_cluster_px : int
        行内窄簇筛选上限（像素）。仅用于从混合型连通域逐行选取"纵沟候选簇"，
        通常设为 2 × nominal_px，防止跳到斜线/宽干扰域。
        不作为最终计数的宽度上限。
    img_h : int
        图像高度（像素），保留供后续扩展使用。
    edge_margin_px : int
        左右边缘各排除的列数。默认 0（不排除）。
    min_segment_len_px : int
        连续线段的最小纵向长度阈值（像素）。
    max_angle_deg : float
        允许相邻行偏转的最大角度（度）；超出则切割子段。

    Returns
    -------
    (positions, count, line_mask, widths)
        positions : list[float]   各线条子段逐行中心 X 均值（升序）
        count     : int           有效线条数量
        line_mask : np.ndarray    纵向线条掩码（255=线条，0=背景）
        widths    : list[float]   各线条逐行均值宽度（与 positions 对应）
    """
    work_binary = binary.copy()
    img_w = binary.shape[1]

    # ── 屏蔽左右边缘列（主沟残留区域） ──────────────────────────────
    if edge_margin_px > 0:
        work_binary[:, :edge_margin_px] = 0
        work_binary[:, max(0, img_w - edge_margin_px):] = 0

    # ── 桥接交替明暗纹理造成的小竖向断点 ─────────────────────────────
    bridged = _bridge_small_vertical_gaps(work_binary, max_gap_px=4)

    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        (bridged > 0).astype(np.uint8), connectivity=8
    )

    line_mask = np.zeros_like(binary)
    pairs: List[Tuple[float, float]] = []

    for label_id in range(1, n_labels):
        left       = int(stats[label_id, cv2.CC_STAT_LEFT])
        top        = int(stats[label_id, cv2.CC_STAT_TOP])
        bbox_width = int(stats[label_id, cv2.CC_STAT_WIDTH])
        height     = int(stats[label_id, cv2.CC_STAT_HEIGHT])

        # 快速粗滤：整个 bbox 高度不够，其所有子段也不够
        if height < min_segment_len_px:
            continue

        # ── 逐行提取 (row, center_x, row_width) ──────────────────────
        # 若一行内同时存在多个像素簇（纵沟与斜线共存于同一连通域），
        # 优先使用宽度 ≤ narrow_cluster_px 的窄簇计算 center_x 和 row_width，
        # 避免斜线像素将行跨度拉宽，导致 center_x 偏移触发误切割。
        # 多个窄簇时，追踪与上一行 center_x 最近的一个（位置连续性），
        # 而非选最窄的（防止跳变到对角线产生的细小右侧簇）。
        row_data: List[Tuple[int, float, float]] = []
        prev_groove_cx: Optional[float] = None
        for row in range(top, top + height):
            cols = np.where(
                labels[row, left : left + bbox_width + 1] == label_id
            )[0]
            if len(cols) == 0:
                continue
            # 将行内像素按列切割为连续簇（相邻列间隙 > 2px 则分割）
            row_clusters: List[Tuple[int, int]] = []  # (abs_col_left, abs_col_right)
            seg_c = int(cols[0])
            for i in range(1, len(cols)):
                if int(cols[i]) - int(cols[i - 1]) > 2:
                    row_clusters.append((seg_c + left, int(cols[i - 1]) + left))
                    seg_c = int(cols[i])
            row_clusters.append((seg_c + left, int(cols[-1]) + left))
            # 筛选宽度 ≤ narrow_cluster_px 的窄簇（防止跳到斜线/宽干扰域）
            narrow_clusters = [
                (c0, c1) for c0, c1 in row_clusters if (c1 - c0 + 1) <= narrow_cluster_px
            ]
            if narrow_clusters:
                if prev_groove_cx is not None and len(narrow_clusters) > 1:
                    # 多窄簇：选中心 x 最接近上一行的（保持位置连续性）
                    c0, c1 = min(
                        narrow_clusters,
                        key=lambda c: abs((c[0] + c[1]) / 2.0 - prev_groove_cx),
                    )
                else:
                    # 单窄簇或首行：取最左侧（cols 已按列升序）
                    c0, c1 = narrow_clusters[0]
            else:
                # 全部过宽：退化为整行跨度（后续宽度过滤会拒绝此行）
                c0, c1 = row_clusters[0][0], row_clusters[-1][1]
            cx = float(c0 + c1) / 2.0
            rw = float(c1 - c0 + 1)
            prev_groove_cx = cx
            row_data.append((row, cx, rw))

        if not row_data:
            continue

        # ── 按局部坡度切割为若干近竖直子段 ──────────────────────────
        sub_segs = _split_row_data_by_angle(row_data, max_angle_deg)

        for seg in sub_segs:
            if not seg:
                continue

            first_row, last_row = seg[0][0], seg[-1][0]
            seg_height = last_row - first_row + 1

            # ① 子段高度过滤
            if seg_height < min_segment_len_px:
                logger.debug(
                    "label=%d 子段 rows=[%d,%d] 高度 %dpx < min %dpx，跳过",
                    label_id, first_row, last_row, seg_height, min_segment_len_px,
                )
                continue

            # ② 逐行均值宽度过滤（仅下限，无上限约束）
            mean_w = float(np.mean([rw for (_, _, rw) in seg]))
            if mean_w < min_w_px:
                logger.debug(
                    "label=%d 子段 rows=[%d,%d] 均值宽 %.1fpx < 下限 %dpx，跳过",
                    label_id, first_row, last_row, mean_w, min_w_px,
                )
                continue

            logger.debug(
                "接受 label=%d 子段 rows=[%d,%d] h=%d mean_row_w=%.1fpx",
                label_id, first_row, last_row, seg_height, mean_w,
            )

            # 标记 line_mask（仅标记该子段各行的纵沟窄簇位置）
            for row, cx, rw in seg:
                c0 = max(0, int(round(cx - rw / 2.0)))
                c1 = min(line_mask.shape[1] - 1, int(round(cx + rw / 2.0)))
                line_mask[row, c0 : c1 + 1] = 255

            # 线条位置：子段各行中心 x 均值
            center_x = float(np.mean([cx for (_, cx, _) in seg]))
            pairs.append((center_x, float(mean_w)))

    pairs.sort(key=lambda item: item[0])
    if pairs:
        positions = [p for p, _ in pairs]
        widths    = [w for _, w in pairs]
    else:
        positions, widths = [], []

    return positions, len(pairs), line_mask, widths


def _draw_debug_image(
    image: np.ndarray,
    line_mask: np.ndarray,
    positions: List[float],
    widths: List[float],
    rib_type: str,
    count: int,
    max_count: int,
    is_valid: bool,
) -> np.ndarray:
    """
    在原图上叠加纵向线条掩码和文字标注，生成用于调试的 BGR 图。

    - 蓝色半透明遮罩：检测到的纵向线条区域
    - 竖线：各线条中心（绿色=合规，红色=违规）
    - 左上角文字：RIB 类型、线条数量 / 允许上限
    """
    debug = image.copy()

    # 叠加蓝色半透明掩码标示检测到的线条区域
    overlay = np.zeros_like(debug)
    overlay[line_mask > 0] = (200, 100, 0)
    debug = cv2.addWeighted(debug, 0.7, overlay, 0.3, 0)

    # 在每条线条中心绘制竖线标记
    h          = debug.shape[0]
    line_color = (0, 255, 0) if is_valid else (0, 0, 255)  # 绿=合规, 红=违规
    for x in positions:
        cv2.line(debug, (int(round(x)), 0), (int(round(x)), h - 1), line_color, 1)

    # 文字标注（左上角）
    font      = cv2.FONT_HERSHEY_SIMPLEX
    fscale    = 0.35
    fthick    = 1
    txt_color = (255, 255, 255)
    bg_color  = (0, 0, 0)
    labels    = [
        rib_type,
        f"L:{count}/{max_count} {'OK' if is_valid else 'NG'}",
    ]
    y_cur = 10
    for label in labels:
        (tw, th), _ = cv2.getTextSize(label, font, fscale, fthick)
        cv2.rectangle(debug, (1, y_cur - th - 1), (3 + tw, y_cur + 2), bg_color, -1)
        cv2.putText(debug, label, (2, y_cur), font, fscale, txt_color, fthick, cv2.LINE_AA)
        y_cur += th + 4

    return debug
