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

from utils.logger import get_logger
from utils.exceptions import PatternDetectionError, ImageDimensionError
from configs.rules_config import LongitudinalGroovesConfig

logger = get_logger("detect_longitudinal_grooves")

# ============================================================
# 模块级默认配置
# ============================================================

_DEFAULT_CFG = LongitudinalGroovesConfig()


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
    max_width_factor: float = 3.0,
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
    max_width_factor : float
        宽度上限倍数（相对名义宽度）。子段逐行均值宽度超过
        ``nominal_px × max_width_factor`` 时被判定为非纵沟特征并排除。
        默认 3.0（约 12px @ 4px 名义宽度）。

    Returns
    -------
    score : float
        评分。满足数量约束 → 4.0，否则 → 0.0。
        检测失败时返回 ``None``。
    details : dict
        成功时包含以下键：

        - ``rib_type``        (*str*)             ：RIB 类型，``"RIB2/3/4"`` 或 ``"RIB1/5"``
        - ``groove_count``    (*int*)             ：检测到的纵向线条数量
        - ``groove_positions``(*list[float]*)     ：各线条中心 X 坐标（升序，像素）
        - ``groove_widths``   (*list[float]*)     ：各线条宽度（像素，与 positions 对应）
        - ``is_valid``        (*bool*)            ：数量是否在允许范围内
        - ``score``           (*float*)           ：同返回值 score
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
            raise PatternDetectionError("图像数据为 None")

        if image.ndim != 3 or image.shape[2] != 3:
            raise ImageDimensionError(
                "(H, W, 3)", image.shape, "BGR 输入图像"
            )

        image_type = image_type.strip().lower()
        if image_type not in _DEFAULT_CFG.rib_label:
            raise PatternDetectionError(
                f"未知的 image_type '{image_type}'，应为 'center' 或 'side'"
            )

        # ── 参数准备 ───────────────────────────────────────────────────
        nominal_px = groove_width_mm * pixel_per_mm
        min_w_px          = max(1, int(round(nominal_px)) - min_width_offset_px)
        max_w_px          = max(int(round(nominal_px * max_width_factor)), min_w_px + 2)
        narrow_cluster_px = max(min_w_px + 1, int(round(nominal_px * 3)))  # 仅用于行内窄簇筛选
        dedup_dist_px     = nominal_px * 2.0  # 去重距离（中心 x 差 < 此值则合并）
        rib_type   = _DEFAULT_CFG.rib_label[image_type]
        max_count  = _DEFAULT_CFG.max_count[image_type]
        img_h, img_w = image.shape[:2]

        edge_margin_px = max(0, int(img_w * edge_margin_ratio))
        min_segment_len_px = max(1, int(np.ceil(img_w * min_segment_length_ratio)))
        logger.debug(
            "rib_type=%s, nominal_px=%.1f, w_range=[%d,%d]px, min_seg=%d, max_count=%d, edge=%d, angle=%.0f",
            rib_type, nominal_px, min_w_px, max_w_px, min_segment_len_px, max_count, edge_margin_px, max_angle_deg,
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
            min_segment_len_px, max_angle_deg, max_w_px, dedup_dist_px,
        )
        logger.debug("纵向线条数量=%d, 位置=%s", count, positions)

        # ── Step 4: 合规判定与评分 ────────────────────────────────────
        score_val = _compute_score(count, max_count, _DEFAULT_CFG.score)
        is_valid  = score_val > 0

        # ── Step 5: 生成调试标注图 ────────────────────────────────────
        debug_image = _draw_debug_image(
            image, line_mask, positions, widths,
            rib_type, count, max_count, is_valid, score_val,
        )

        details: Dict[str, Any] = {
            "rib_type":        rib_type,
            "groove_count":    count,
            "groove_positions": positions,
            "groove_widths":   widths,
            "is_valid":        is_valid,
            "score":           float(score_val),
            "line_mask":       line_mask,
            "debug_image":     debug_image,
        }
        logger.debug("纵向线条检测完成，score=%.1f, is_valid=%s", score_val, is_valid)
        return float(score_val), details

    except Exception as exc:
        err_msg    = str(exc)
        error_type = type(exc).__name__
        logger.error("纵向线条检测失败：%s", err_msg)
        return None, {"err_msg": err_msg, "error_type": error_type}


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


def _build_groove_tracks(
    all_row_clusters: List[Tuple[int, List[Tuple[int, int]]]],
    max_dx: float = 8.0,
    max_gap_rows: int = 5,
) -> List[List[Tuple[int, float, float]]]:
    """
    从逐行窄簇数据构建多条平行沟槽轨迹。

    对每一行的窄簇，尝试与已有活动轨迹匹配（按中心 x 最近原则贪心）。
    未匹配的簇启动新轨迹；超过 *max_gap_rows* 行未匹配的轨迹关闭。

    Parameters
    ----------
    all_row_clusters : list of (row, [(c0, c1), ...])
        每行的窄簇列表（绝对列坐标），按行升序。
    max_dx : float
        匹配容差（像素），簇中心与轨迹末端中心差 ≤ max_dx 才匹配。
    max_gap_rows : int
        轨迹允许的最大行间隙。

    Returns
    -------
    list of tracks, 每条轨迹为 [(row, center_x, width), ...]
    """
    active: List[dict] = []          # {"data": [...], "last_row": int, "last_cx": float}
    finished: List[List[Tuple[int, float, float]]] = []

    for row, clusters in all_row_clusters:
        cluster_info = [((c0 + c1) / 2.0, float(c1 - c0 + 1)) for c0, c1 in clusters]

        # 关闭超时轨迹
        still_active: List[dict] = []
        for trk in active:
            if row - trk["last_row"] > max_gap_rows:
                finished.append(trk["data"])
            else:
                still_active.append(trk)
        active = still_active

        # 贪心匹配（按距离排序，距离最近者优先配对）
        candidates = []
        for ti, trk in enumerate(active):
            for ci, (cx, _w) in enumerate(cluster_info):
                dist = abs(cx - trk["last_cx"])
                if dist <= max_dx:
                    candidates.append((dist, ti, ci))
        candidates.sort()

        matched_tracks: set = set()
        matched_clusters: set = set()
        for dist, ti, ci in candidates:
            if ti in matched_tracks or ci in matched_clusters:
                continue
            cx, w = cluster_info[ci]
            active[ti]["data"].append((row, cx, w))
            active[ti]["last_row"] = row
            active[ti]["last_cx"] = cx
            matched_tracks.add(ti)
            matched_clusters.add(ci)

        # 未匹配簇 → 新轨迹
        for ci, (cx, w) in enumerate(cluster_info):
            if ci not in matched_clusters:
                active.append({"data": [(row, cx, w)], "last_row": row, "last_cx": cx})

    # 收尾：关闭所有剩余活动轨迹
    for trk in active:
        finished.append(trk["data"])
    return finished


def _analyze_vertical_lines(
    binary: np.ndarray,
    min_w_px: int,
    narrow_cluster_px: int,
    img_h: int,
    edge_margin_px: int = 0,
    min_segment_len_px: int = 1,
    max_angle_deg: float = 30.0,
    max_w_px: int = 12,
    dedup_dist_px: float = 8.0,
) -> Tuple[List[float], int, np.ndarray, List[float]]:
    """
    通过连通域分析识别纵向线条（多路径追踪 + 宽度上限 + 去重）。

    核心流程
    --------
    1. 屏蔽边缘 → 桥接小间隙 → 连通域分析
    2. 对每个连通域，逐行提取 **所有** 窄簇（≤ narrow_cluster_px）
    3. 调用 ``_build_groove_tracks`` 同时追踪多条平行沟槽轨迹
    4. 每条轨迹经 ``_split_row_data_by_angle`` 角度切割
    5. 子段通过高度、宽度下限和上限过滤后，计为有效纵沟
    6. 最后对中心位置过近的结果去重合并

    Parameters
    ----------
    binary : np.ndarray
        自适应二值化图像（暗色线条 = 白色前景）。
    min_w_px : int
        纵向线条最小宽度（像素，逐行均值）。
    narrow_cluster_px : int
        行内窄簇筛选上限（像素）。
    img_h : int
        图像高度（像素）。
    edge_margin_px : int
        左右边缘各排除的列数。
    min_segment_len_px : int
        连续线段的最小纵向长度阈值（像素）。
    max_angle_deg : float
        允许相邻行偏转的最大角度（度）。
    max_w_px : int
        纵向线条最大宽度（像素，逐行均值）。超过则判定为非纵沟特征。
    dedup_dist_px : float
        去重距离（像素）。中心 x 差 < 此值的结果合并为一条。

    Returns
    -------
    (positions, count, line_mask, widths)
        positions : list[float]   各线条中心 X 均值（升序）
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

    # ── 形态学垂直开运算：桥接后去除散乱纹理噪声 ─────────────────────
    # 先桥接修复纵向线条中的小间隙，再用较高的垂直核做开运算，
    # 要求特征在单列内有足够连续的垂直前景像素才能存活，
    # 有效将大面积噪声 CC 中的纵沟信号分离出来。
    # 核高度自适应：取 min_seg/2 与"最大允许倾斜角线条的单列垂直跨度"的较小值，
    # 保证不会因形态学操作而误杀仍在角度容差范围内的倾斜线条。
    if 0 < max_angle_deg < 85:
        _max_tilt_vert = int(min_w_px / np.tan(np.radians(max_angle_deg)))
    else:
        _max_tilt_vert = min_segment_len_px
    _vert_open_h = max(3, min(_max_tilt_vert, min_segment_len_px // 2))
    _open_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, _vert_open_h))
    bridged = cv2.morphologyEx(bridged, cv2.MORPH_OPEN, _open_kernel)

    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        (bridged > 0).astype(np.uint8), connectivity=8
    )

    line_mask = np.zeros_like(binary)
    # (center_x, mean_w, first_row, last_row) — 包含行范围用于智能去重
    raw_segments: List[Tuple[float, float, int, int]] = []

    for label_id in range(1, n_labels):
        left       = int(stats[label_id, cv2.CC_STAT_LEFT])
        top        = int(stats[label_id, cv2.CC_STAT_TOP])
        bbox_width = int(stats[label_id, cv2.CC_STAT_WIDTH])
        height     = int(stats[label_id, cv2.CC_STAT_HEIGHT])

        # 快速粗滤：整个 bbox 高度不够，其所有子段也不够
        if height < min_segment_len_px:
            continue

        # ── 逐行提取所有窄簇 ──────────────────────────────────────
        all_row_clusters: List[Tuple[int, List[Tuple[int, int]]]] = []
        for row in range(top, top + height):
            cols = np.where(
                labels[row, left : left + bbox_width + 1] == label_id
            )[0]
            if len(cols) == 0:
                continue
            # 将行内像素按列切割为连续簇（相邻列间隙 > 2px 则分割）
            row_clusters: List[Tuple[int, int]] = []
            seg_c = int(cols[0])
            for i in range(1, len(cols)):
                if int(cols[i]) - int(cols[i - 1]) > 2:
                    row_clusters.append((seg_c + left, int(cols[i - 1]) + left))
                    seg_c = int(cols[i])
            row_clusters.append((seg_c + left, int(cols[-1]) + left))
            # 筛选宽度 ≤ narrow_cluster_px 的窄簇
            narrow = [
                (c0, c1) for c0, c1 in row_clusters if (c1 - c0 + 1) <= narrow_cluster_px
            ]
            if narrow:
                all_row_clusters.append((row, narrow))

        if not all_row_clusters:
            continue

        # ── 多路径追踪：同时追踪同一连通域内的多条平行沟槽 ──────────
        tracks = _build_groove_tracks(
            all_row_clusters, max_dx=narrow_cluster_px, max_gap_rows=5,
        )

        for track_data in tracks:
            # 按局部坡度切割为若干近竖直子段
            sub_segs = _split_row_data_by_angle(track_data, max_angle_deg)

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

                # ② 逐行均值宽度过滤（下限）
                mean_w = float(np.mean([rw for (_, _, rw) in seg]))
                if mean_w < min_w_px:
                    logger.debug(
                        "label=%d 子段 rows=[%d,%d] 均值宽 %.1fpx < 下限 %dpx，跳过",
                        label_id, first_row, last_row, mean_w, min_w_px,
                    )
                    continue

                # ③ 逐行均值宽度过滤（上限，排除花纹边缘等宽特征）
                if mean_w > max_w_px:
                    logger.debug(
                        "label=%d 子段 rows=[%d,%d] 均值宽 %.1fpx > 上限 %dpx，跳过",
                        label_id, first_row, last_row, mean_w, max_w_px,
                    )
                    continue

                logger.debug(
                    "接受 label=%d 子段 rows=[%d,%d] h=%d mean_row_w=%.1fpx",
                    label_id, first_row, last_row, seg_height, mean_w,
                )

                # 标记 line_mask
                for row, cx, rw in seg:
                    c0 = max(0, int(round(cx - rw / 2.0)))
                    c1 = min(line_mask.shape[1] - 1, int(round(cx + rw / 2.0)))
                    line_mask[row, c0 : c1 + 1] = 255

                center_x = float(np.mean([cx for (_, cx, _) in seg]))
                raw_segments.append((center_x, float(mean_w), first_row, last_row))

    # ── 排序 + 智能去重（仅合并 x 相近 且 行范围重叠 的结果）───────────
    # 同一 x 位置不同行范围的子段视为不同沟槽分别计数。
    raw_segments.sort(key=lambda item: item[0])
    deduped: List[Tuple[float, float, int, int]] = []
    for cx, w, r0, r1 in raw_segments:
        merged = False
        for i, (dcx, dw, dr0, dr1) in enumerate(deduped):
            if abs(cx - dcx) < dedup_dist_px:
                # 行范围重叠比 > 50% 才视为重复
                overlap = max(0, min(r1, dr1) - max(r0, dr0) + 1)
                min_span = min(r1 - r0 + 1, dr1 - dr0 + 1)
                if min_span > 0 and overlap / min_span > 0.5:
                    deduped[i] = ((dcx + cx) / 2.0, max(dw, w),
                                  min(dr0, r0), max(dr1, r1))
                    merged = True
                    break
        if not merged:
            deduped.append((cx, w, r0, r1))

    if deduped:
        positions = [p for p, _, _, _ in deduped]
        widths    = [w for _, w, _, _ in deduped]
    else:
        positions, widths = [], []

    return positions, len(deduped), line_mask, widths


def _compute_score(count: int, max_count: int, max_score: int) -> int:
    """
    根据检测数量和允许上限计算得分。

    ``count <= max_count`` → ``max_score``；否则 → ``0``。
    """
    return max_score if count <= max_count else 0


def _draw_debug_image(
    image: np.ndarray,
    line_mask: np.ndarray,
    positions: List[float],
    widths: List[float],
    rib_type: str,
    count: int,
    max_count: int,
    is_valid: bool,
    score: float,
) -> np.ndarray:
    """
    在原图上叠加纵向线条掩码和文字标注，生成用于调试的 BGR 图。

    - 蓝色半透明遮罩：检测到的纵向线条区域
    - 竖线：各线条中心（绿色=合规，红色=违规）
    - 左上角文字：RIB 类型、线条数量 / 允许上限、评分
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
        f"S:{score:.0f}",
    ]
    y_cur = 10
    for label in labels:
        (tw, th), _ = cv2.getTextSize(label, font, fscale, fthick)
        cv2.rectangle(debug, (1, y_cur - th - 1), (3 + tw, y_cur + 2), bg_color, -1)
        cv2.putText(debug, label, (2, y_cur), font, fscale, txt_color, fthick, cv2.LINE_AA)
        y_cur += th + 4

    return debug
