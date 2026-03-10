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

# Copyright © 2026. All rights reserved.
# Author: 桂禹
# AI Assistant: ClaudeCode (Claude Sonnet 4.6)

import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from utils.logger import get_logger
from utils.exceptions import PatternDetectionError, ImageDimensionError

logger = get_logger("detect_transverse_grooves")

# ============================================================
# 常量
# ============================================================

# image_type → RIB 标签
_RIB_LABEL: Dict[str, str] = {
    "center": "RIB1/5",
    "side":   "RIB2/3/4",
}

# 各类型默认最小横沟厚度（mm）
_DEFAULT_GROOVE_WIDTH_MM: Dict[str, float] = {
    "center": 3.5,
    "side":   1.8,
}

# 各要求满分
_MAX_SCORE_REQ8  = 4   # 需求8：横沟数量
_MAX_SCORE_REQ14 = 2   # 需求14：交叉点数量


# ============================================================
# 主函数
# ============================================================

def detect_transverse_grooves(
    image: np.ndarray,
    image_type: str,
    groove_width_mm: Optional[Dict[str, float]] = None,
    pixel_per_mm: float = 7.1,
    max_intersections: int = 2,
) -> Tuple[float, Dict[str, Any]]:
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
    score : float
        综合评分（需求8最高 4 分 + 需求14最高 2 分）。
    details : dict
        详细分析结果，包含以下键：

        - ``rib_type`` (*str*)：RIB 类型，``"RIB1/5"`` 或 ``"RIB2/3/4"``
        - ``groove_count`` (*int*)：检测到的横沟数量
        - ``intersection_count`` (*int*)：与纵向线条的交叉点数量
        - ``is_valid`` (*bool*)：是否同时满足需求8与需求14
        - ``groove_mask`` (*ndarray*)：横沟掩码（白色为横沟前景）
        - ``groove_positions`` (*list[float]*)：各横沟中心 Y 坐标（升序）
        - ``score_req8`` (*float*)：需求8得分
        - ``score_req14`` (*float*)：需求14得分
        - ``debug_image`` (*ndarray*)：BGR 标注图

    Raises
    ------
    PatternDetectionError
        图像数据为 None 或检测过程中发生未预期错误时。
    ImageDimensionError
        图像不是三通道 BGR 数组时。
    """
    try:
        logger.debug("开始横沟检测，image_type=%s", image_type)

        # ── 输入验证 ──────────────────────────────────────────────────
        if image is None:
            raise PatternDetectionError("图像数据为 None")

        if image.ndim != 3 or image.shape[2] != 3:
            raise ImageDimensionError(
                "(H, W, 3)", image.shape, "BGR 输入图像"
            )

        image_type = image_type.strip().lower()
        if image_type not in _RIB_LABEL:
            raise PatternDetectionError(
                f"未知的 image_type '{image_type}'，应为 'center' 或 'side'"
            )

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
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=15, C=5,
        )

        # ── Step 3: 水平形态学开运算提取横向带状区域 ─────────────────
        # X 方向宽度：强制水平延伸；最少 3× groove_px，上限图像宽度的 2/3
        horiz_px = min(img_w * 2 // 3, max(groove_px * 3, 24))
        # Y 方向高度：groove_px 确保只保留厚度 ≥ 横沟最小宽度的区域
        se = cv2.getStructuringElement(cv2.MORPH_RECT, (horiz_px, groove_px))
        groove_mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, se)

        # 轻微垂直膨胀，将同一横沟的相邻行合并为完整连通域
        groove_mask = cv2.dilate(
            groove_mask,
            cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3)),
        )

        # ── Step 4: 连通域分析统计横沟数量与位置 ─────────────────────
        groove_positions, groove_count = _analyze_grooves(
            groove_mask, groove_px, img_w
        )
        logger.debug("横沟数量=%d, 位置=%s", groove_count, groove_positions)

        # ── Step 5: 骨架分析统计与纵向线条的交叉点数量 ───────────────
        intersection_count = _count_intersections(binary, groove_mask)
        logger.debug("交叉点数量=%d", intersection_count)

        # ── Step 6: 合规判定与评分 ────────────────────────────────────
        score_8, score_14 = _compute_scores(
            rib_type, groove_count, intersection_count, max_intersections
        )
        score      = float(score_8 + score_14)
        is_valid   = (score_8 == _MAX_SCORE_REQ8) and (score_14 == _MAX_SCORE_REQ14)

        # ── Step 7: 生成调试标注图 ────────────────────────────────────
        debug_image = _draw_debug_image(
            image, groove_mask, groove_positions,
            rib_type, groove_count, intersection_count,
            score_8 == _MAX_SCORE_REQ8, score_14 == _MAX_SCORE_REQ14, score,
        )

        details: Dict[str, Any] = {
            "rib_type":           rib_type,
            "groove_count":       groove_count,
            "intersection_count": intersection_count,
            "is_valid":           is_valid,
            "groove_mask":        groove_mask,
            "groove_positions":   groove_positions,
            "score_req8":         float(score_8),
            "score_req14":        float(score_14),
            "debug_image":        debug_image,
        }
        logger.debug("横沟检测完成，score=%.1f, is_valid=%s", score, is_valid)
        return score, details

    except (PatternDetectionError, ImageDimensionError):
        raise
    except Exception as exc:
        raise PatternDetectionError(f"横沟检测失败: {exc}") from exc


# ============================================================
# 内部辅助函数
# ============================================================

def _analyze_grooves(
    groove_mask: np.ndarray,
    groove_px: int,
    img_w: int,
) -> Tuple[List[float], int]:
    """
    对横沟掩码做连通域分析，过滤掉宽高比不合理的噪声，
    返回各横沟的中心 Y 坐标列表（升序）和数量。

    条件：
    - 连通域宽度 > 高度（横向延伸）
    - 面积 ≥ groove_px × img_w // 4（排除极小噪声）
    """
    num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(
        groove_mask, connectivity=8
    )
    min_area = groove_px * (img_w // 4)
    positions: List[float] = []

    for i in range(1, num_labels):   # 0 为背景
        w    = stats[i, cv2.CC_STAT_WIDTH]
        h    = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]
        if w > h and area >= min_area:
            positions.append(float(centroids[i][1]))   # Y 坐标

    positions.sort()
    return positions, len(positions)


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
    统计横沟与纵向线条的交叉点数量。

    流程：
    1. 对完整二值图做骨架化提取，获取单像素宽的线条网络。
    2. 用 8 邻域计数核统计每个骨架像素的邻居数。
    3. 邻居数 ≥ 3 的骨架像素为分叉点（T/Y/X 型交叉）。
    4. 将分叉点限制在横沟区域（含少量向外膨胀以容忍骨架偏移）。
    5. 对邻近分叉点团块做膨胀合并，再用连通域计数得到交叉点个数。

    Parameters
    ----------
    binary : np.ndarray
        全特征二值图（暗色沟槽 = 白色前景）。
    groove_mask : np.ndarray
        横沟掩码。

    Returns
    -------
    int
        交叉点数量。
    """
    skeleton = _skeletonize(binary)
    skel_u8  = (skeleton > 0).astype(np.uint8)

    # 8 邻域邻居计数（不含自身）
    nbr_kernel   = np.ones((3, 3), dtype=np.float32)
    nbr_kernel[1, 1] = 0.0
    nbr_count    = cv2.filter2D(skel_u8.astype(np.float32), -1, nbr_kernel)

    # 分叉点：骨架像素 且 8 邻域中骨架数 ≥ 3
    junction_map = (skel_u8 > 0) & (nbr_count >= 3)

    # 限定在横沟区域内（稍微膨胀以容忍骨架单像素偏移）
    groove_region = cv2.dilate(groove_mask, np.ones((7, 7), np.uint8)) > 0
    in_groove     = junction_map & groove_region

    if not np.any(in_groove):
        return 0

    # 膨胀合并相邻分叉点 → 每个真实交叉点对应一个连通域
    junc_u8   = (in_groove * 255).astype(np.uint8)
    junc_u8   = cv2.dilate(junc_u8, np.ones((5, 5), np.uint8))
    n_labels, _ = cv2.connectedComponents(junc_u8, connectivity=8)

    return max(0, n_labels - 1)   # 减去背景标签


def _compute_scores(
    rib_type: str,
    groove_count: int,
    intersection_count: int,
    max_intersections: int,
) -> Tuple[int, int]:
    """
    计算需求8和需求14的得分。

    需求8（横沟数量）
      - RIB1/5  ：count == 1 → 4 分，否则 0 分
      - RIB2/3/4：count <= 1 → 4 分，否则 0 分

    需求14（交叉点数量）
      - intersection_count <= max_intersections → 2 分，否则 0 分

    Returns
    -------
    (score_8, score_14)
    """
    if rib_type == "RIB1/5":
        score_8 = _MAX_SCORE_REQ8 if groove_count == 1 else 0
    else:   # RIB2/3/4
        score_8 = _MAX_SCORE_REQ8 if groove_count <= 1 else 0

    score_14 = _MAX_SCORE_REQ14 if intersection_count <= max_intersections else 0
    return score_8, score_14


def _draw_debug_image(
    image: np.ndarray,
    groove_mask: np.ndarray,
    groove_positions: List[float],
    rib_type: str,
    groove_count: int,
    intersection_count: int,
    valid_8: bool,
    valid_14: bool,
    score: float,
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

    # 在每个横沟中心绘制水平线
    h, w        = debug.shape[:2]
    line_color  = (0, 255, 0) if valid_8 else (0, 0, 255)
    for y in groove_positions:
        cv2.line(debug, (0, int(round(y))), (w - 1, int(round(y))), line_color, 1)

    # 文字标注（左上角）
    font       = cv2.FONT_HERSHEY_SIMPLEX
    fscale     = 0.35
    fthick     = 1
    txt_color  = (255, 255, 255)
    bg_color   = (0, 0, 0)
    lines      = [
        rib_type,
        f"G:{groove_count} {'OK' if valid_8  else 'NG'}",
        f"X:{intersection_count} {'OK' if valid_14 else 'NG'}",
        f"S:{score:.0f}",
    ]
    y_cur = 10
    for line in lines:
        (tw, th), _ = cv2.getTextSize(line, font, fscale, fthick)
        cv2.rectangle(debug, (1, y_cur - th - 1), (3 + tw, y_cur + 2), bg_color, -1)
        cv2.putText(debug, line, (2, y_cur), font, fscale, txt_color, fthick, cv2.LINE_AA)
        y_cur += th + 4

    return debug
