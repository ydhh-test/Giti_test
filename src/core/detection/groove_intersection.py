# -*- coding: utf-8 -*-

"""
横沟检测模块

检测小图中横向粗线条（横沟）的位置和数量，
同时分析横沟与纵向细线条的交叉点数量。
支持 center 类型（RIB1/5）和 side 类型（RIB2/3/4），
按各自宽度标准与数量约束进行合规判定与综合评分。

评分规则：
- 需求8（横沟数量合规）：最高 4 分
- 需求14（交叉点数量 ≤ max_intersections）：最高 2 分
- 总分：最高 6 分
"""

import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

import logging
from src.common.exceptions import InputDataError, RuntimeProcessError

logger = logging.getLogger(__name__)

# ============================================================
# 常量
# ============================================================

# 模块级默认配置（groove_width_mm / score / rib_label 等）
# 均由 TransverseGroovesConfig 统一管理，不在此处重复硬编码
# 算法层默认常量（不依赖 configs，由规则层调用时通过参数传入）
_RIB_LABEL: dict = {"center": "RIB1/5", "side": "RIB2/3/4"}
_DEFAULT_GROOVE_WIDTH_MM: dict = {"center": 3.5, "side": 1.8}


# ============================================================
# 主函数
# ============================================================

def detect_transverse_grooves(
    image: np.ndarray,
    image_type: str,
    groove_width_mm: Optional[Dict[str, float]] = None,
    pixel_per_mm: float = 7.1,
    max_intersections: int = 2,
) -> Dict[str, Any]:
    """
    检测横向粗线条（横沟）的位置、数量及与纵向线条的交叉点数量。

    Parameters
    ----------
    image : np.ndarray
        BGR 图像数组，期望尺寸 (128, 128, 3)。
    image_type : str
        小图类型，``"center"``（对应 RIB1/5）或 ``"side"``（对应 RIB2/3/4）。
    groove_width_mm : dict, optional
        各类型的最小横沟厚度（mm）。
        默认 ``{"center": 3.5, "side": 1.8}``。
    pixel_per_mm : float
        图像像素密度（px/mm），默认 7.1。
    max_intersections : int
        需求14允许的最大交叉点数，默认 2。

    Returns
    -------
    details : dict
        成功时包含以下键：

        - ``rib_type`` (*str*)：RIB 类型，``"RIB1/5"`` 或 ``"RIB2/3/4"``
        - ``groove_count`` (*int*)：检测到的横沟数量
        - ``intersection_count`` (*int*)：与纵向线条的交叉点数量
        - ``is_valid`` (*bool*)：合规判断（恒为 True，正式评分由规则层负责）
        - ``groove_mask`` (*ndarray*)：横沟掩码（白色为横沟前景）
        - ``groove_positions`` (*list[float]*)：各横沟中心 Y 坐标（升序）
        - ``debug_image`` (*ndarray*)：BGR 标注图

        失败时仅包含：

        - ``err_msg`` (*str*)：错误描述
        - ``error_type`` (*str*)：异常类型名称
    """
    try:
        logger.debug("开始横沟检测，image_type=%s", image_type)

        # ── 输入验证 ──────────────────────────────────────────────────
        if image is None:
            raise InputDataError("image", "value", "must not be None")

        if image.ndim != 3 or image.shape[2] != 3:
            raise InputDataError("image", "shape", "expected (H, W, 3)", image.shape)

        image_type = image_type.strip().lower()
        if image_type not in _RIB_LABEL:
            raise InputDataError("image_type", "value", "must be 'center' or 'side'", image_type)

        # ── 参数准备 ───────────────────────────────────────────────────
        widths     = groove_width_mm if groove_width_mm is not None else _DEFAULT_GROOVE_WIDTH_MM
        min_w_mm   = widths.get(image_type, _DEFAULT_GROOVE_WIDTH_MM[image_type])
        groove_px  = max(1, int(round(min_w_mm * pixel_per_mm)))
        rib_type   = _RIB_LABEL[image_type]
        img_h, img_w = image.shape[:2]

        logger.debug("rib_type=%s, groove_px=%d (%.1fmm @ %.1fpx/mm)",
                     rib_type, groove_px, min_w_mm, pixel_per_mm)


        # ── Step 1: 灰度转换 + 高斯模糊降噪 ─────────────────────────
        gray    = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # ── Step 2: 自适应二值化（暗色沟槽 → 白色前景）──────────────
        # blockSize=31 提供更大的局部对比度窗口，更适合轮胎纹路图像
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=31, C=5,
        )

        # ── Step 3: 水平投影分析识别横沟带状区域 ─────────────────
        # 逐行统计前景像素密度，对倾斜横沟比形态学开运算更鲁棒
        groove_positions, groove_count, groove_mask = _analyze_grooves(
            binary, groove_px, img_w
        )
        logger.debug("横沟数量=%d, 位置=%s", groove_count, groove_positions)

        # ── Step 5: 骨架分析统计与纵向线条的交叉点数量 ───────────────
        intersection_count = _count_intersections(binary, groove_mask)
        logger.debug("交叉点数量=%d", intersection_count)

        is_valid = True  # 合规判断由规则层负责

        # ── Step 7: 生成调试标注图 ────────────────────────────────────
        debug_image = _draw_debug_image(
            image, groove_mask, groove_positions,
            rib_type, groove_count, intersection_count,
        )

        details: Dict[str, Any] = {
            "rib_type":           rib_type,
            "groove_count":       groove_count,
            "intersection_count": intersection_count,
            "is_valid":           is_valid,
            "groove_mask":        groove_mask,
            "groove_positions":   groove_positions,
            "debug_image":        debug_image,
        }
        logger.debug("横沟检测完成，groove_count=%d, intersection_count=%d", groove_count, intersection_count)
        return details

    except Exception as exc:
        err_msg = str(exc)
        error_type = type(exc).__name__
        logger.error("横沟检测失败：%s", err_msg)
        return {"err_msg": err_msg, "error_type": error_type}


# ============================================================
# 内部辅助函数
# ============================================================

def _analyze_grooves(
    binary: np.ndarray,
    groove_px: int,
    img_w: int,
) -> Tuple[List[float], int, np.ndarray]:
    """
    通过水平投影识别横向带状区域（横沟）。

    逐行统计前景像素密度，将连续的高密度行段聚合为一条横沟。
    对倾斜横沟比形态学开运算更鲁棒：
    不要求前景像素形成实心矩形块。

    Parameters
    ----------
    binary : np.ndarray
        自适应二值化图像（暗色沟槽 = 白色前景）。
    groove_px : int
        横沟最小宽度（像素）。
    img_w : int
        图像宽度（像素）。

    Returns
    -------
    (positions, count, groove_mask)
        positions   : list[float]   各横沟中心 Y 坐标（升序）
        count       : int            横沟数量
        groove_mask : np.ndarray    横沟区域掌码
    """
    # 逐行统计前景像素数
    row_sums = (binary > 0).sum(axis=1)
    # 每行至少需占图像宽度 1/4 的前景像素才算可能的横沟行
    min_px_per_row = max(groove_px, img_w // 4)

    hot = np.where(row_sums >= min_px_per_row)[0]

    # 合并连续行（允许最多 3 行空白，应对斜向横沟像素的锗齿跳变）
    groups: List[List[int]] = []
    for r in hot.tolist():
        if groups and r - groups[-1][-1] <= 3:
            groups[-1].append(r)
        else:
            groups.append([r])

    # 按最小纵向厚度过滤（≥ groove_px / 5，最低 3px）
    min_height = max(3, groove_px // 5)
    valid_groups = [g for g in groups if len(g) >= min_height]

    # 重建 groove_mask（采用各横沟所在行的原始二值像素）
    groove_mask = np.zeros_like(binary)
    for g in valid_groups:
        r_start, r_end = min(g), max(g) + 1
        groove_mask[r_start:r_end, :] = binary[r_start:r_end, :]

    positions = sorted(float(np.mean(g)) for g in valid_groups)
    return positions, len(positions), groove_mask


def _skeletonize(binary: np.ndarray) -> np.ndarray:
    """
    形态学骨架化（迭代细化）。

    使用腐蚀-膨胀差分法逐步剥离外层像素，直至只剩单像素宽度的骨架。

    Parameters
    ----------
    binary : np.ndarray
        二值图（255 = 前景）。

    Returns
    -------
    np.ndarray
        骨架图（255 = 骨架像素）。
    """
    skel    = np.zeros_like(binary)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    img     = binary.copy()

    while True:
        eroded = cv2.erode(img, element)
        temp   = cv2.dilate(eroded, element)
        temp   = cv2.subtract(img, temp)
        skel   = cv2.bitwise_or(skel, temp)
        img    = eroded
        if cv2.countNonZero(img) == 0:
            break

    return skel


def _count_intersections(
    binary: np.ndarray,
    groove_mask: np.ndarray,
) -> int:
    """
    统计横沟与纵向线条（细纵沟/钢片）的交叉点数量（逐横沟双侧密度验证法）。

    设计原理
    --------
    真实纵向线（钢片/细纵沟）贯穿整幅图像高度，在每条横沟的**上方和下方**都有
    稳定的前景信号；而斜向横沟的边缘渗漏、局部纹路噪声等伪影只在横沟的某一侧
    集中出现，无法同时满足双侧密度要求。

    对每条横沟分别执行以下步骤：

    Step A — 双侧列密度卷积核
        分别对横沟上方和下方的外部行计算各列前景密度：
        ``D_above[x] = sum(binary[above_rows, x]) / img_h``（归一化到图像高度）
        ``D_below[x] = sum(binary[below_rows, x]) / img_h``
        两侧均可用时阈值 **15%**（各自独立）；只有一侧时阈值提升至 **25%**。

    Step B — 合并热列（5px 间隔容差），过滤图像边缘聚簇

    Step C — 聚簇 × 该横沟配对计数（每对最多计 1 次）
        粗粒度计数天然处理斜向横沟像素碎片化：无论纵线如何穿过横沟，每对最多 1 次。

    Parameters
    ----------
    binary : np.ndarray
        全特征二值图（暗色沟槽 = 白色前景）。
    groove_mask : np.ndarray
        横沟掩码（_analyze_grooves 输出）。

    Returns
    -------
    int
        交叉点数量。
    """
    img_h, img_w = binary.shape
    gm_row_active = groove_mask.sum(axis=1) > 0   # bool (H,)

    groove_row_idx = np.where(gm_row_active)[0]
    if len(groove_row_idx) == 0:
        return 0

    # ── 提取横沟行组（连续行段，允许 2 行空白）────────────────────────
    groove_row_groups: List[Tuple[int, int]] = []
    gs, ge = int(groove_row_idx[0]), int(groove_row_idx[0])
    for r in groove_row_idx[1:]:
        r = int(r)
        if r - ge <= 2:
            ge = r
        else:
            groove_row_groups.append((gs, ge))
            gs = ge = r
    groove_row_groups.append((gs, ge))

    arange_h    = np.arange(img_h)
    intersections = 0

    for g_r0, g_r1 in groove_row_groups:
        # ── Step A：计算该横沟上下两侧的列密度 ──────────────────────
        above_idx = np.where(~gm_row_active & (arange_h < g_r0))[0]
        below_idx = np.where(~gm_row_active & (arange_h > g_r1))[0]
        n_above, n_below = len(above_idx), len(below_idx)

        if n_above == 0 and n_below == 0:
            continue

        # 两侧均可用：双侧阈值 15%；仅一侧可用：单侧阈值 25%（更严格）
        if n_above > 0 and n_below > 0:
            # 使用向上取整（ceiling）确保 15% 阈值严格成立，避免整除下取整使小样本门槛过低
            ta = max(2, (n_above * 15 + 99) // 100) / img_h
            tb = max(2, (n_below * 15 + 99) // 100) / img_h
            da = (binary[above_idx, :] > 0).sum(axis=0) / img_h
            db = (binary[below_idx, :] > 0).sum(axis=0) / img_h
            hot = (da >= ta) & (db >= tb)
        elif n_above > 0:   # 横沟触及底部边界
            ta = max(2, (n_above * 25 + 99) // 100) / img_h
            da = (binary[above_idx, :] > 0).sum(axis=0) / img_h
            hot = da >= ta
        else:               # 横沟触及顶部边界
            tb = max(2, (n_below * 25 + 99) // 100) / img_h
            db = (binary[below_idx, :] > 0).sum(axis=0) / img_h
            hot = db >= tb

        hot_cols = np.where(hot)[0]
        if len(hot_cols) == 0:
            continue

        # ── Step B：合并相邻热列（5px 间隔容差） ─────────────────────
        vert_clusters: List[Tuple[int, int]] = []
        cs, ce = int(hot_cols[0]), int(hot_cols[0])
        for c in hot_cols[1:]:
            c = int(c)
            if c - ce <= 5:
                ce = c
            else:
                vert_clusters.append((cs, ce))
                cs = ce = c
        vert_clusters.append((cs, ce))

        vert_clusters = [
            (xs, xe) for xs, xe in vert_clusters
            if xs > 0 and xe < img_w - 1
        ]

        # ── Step C：配对计数，每（纵向线聚簇 × 横沟）最多计 1 次 ────
        groove_rows_bin = binary[g_r0:g_r1 + 1, :]
        for xs, xe in vert_clusters:
            if (groove_rows_bin[:, xs:xe + 1] > 0).any():
                intersections += 1

    return intersections




def _draw_debug_image(
    image: np.ndarray,
    groove_mask: np.ndarray,
    groove_positions,
    rib_type: str,
    groove_count: int,
    intersection_count: int,
) -> np.ndarray:
    """
    在原图上叠加横沟掩码和文字标注，生成用于调试的 BGR 图。

    - 绿色半透明遮罩：检测到的横沟区域
    - 水平线：各横沟中心（绿色=合规，红色=违规）
    - 左上角文字：RIB 类型、数量、交叉点数、评分
    """
    debug = image.copy()

    # 叠加绿色半透明掩码
    overlay              = np.zeros_like(debug)
    overlay[groove_mask > 0] = (0, 200, 0)
    debug = cv2.addWeighted(debug, 0.7, overlay, 0.3, 0)

    # 在每个横沟中心绘制水平线（算法层不知道评分，用固定蓝色）
    h, w        = debug.shape[:2]
    line_color  = (0, 200, 255)  # 青色，与评分层解耦
    for y in groove_positions:
        cv2.line(debug, (0, int(round(y))), (w - 1, int(round(y))), line_color, 1)

    # 文字标注（左上角，仅展示原始检测数据，不含评分）
    font       = cv2.FONT_HERSHEY_SIMPLEX
    fscale     = 0.35
    fthick     = 1
    txt_color  = (255, 255, 255)
    bg_color   = (0, 0, 0)
    lines      = [
        rib_type,
        f"G:{groove_count}",
        f"X:{intersection_count}",
    ]
    y_cur = 10
    for line in lines:
        (tw, th), _ = cv2.getTextSize(line, font, fscale, fthick)
        cv2.rectangle(debug, (1, y_cur - th - 1), (3 + tw, y_cur + 2), bg_color, -1)
        cv2.putText(debug, line, (2, y_cur), font, fscale, txt_color, fthick, cv2.LINE_AA)
        y_cur += th + 4

    return debug
