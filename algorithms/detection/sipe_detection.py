# -*- coding: utf-8 -*-

"""
横向钢片检测模块

检测小图中横向细线条（钢片/sipe）的数量和位置，
并按 RIB 类型进行合规判定与综合评分。
支持 center 类型（RIB1/5）和 side 类型（RIB2/3/4），
按各自数量约束进行评分。

评分规则：
- 需求9（钢片数量合规）：最高 4 分
- 需求10（钢片位置均分）：最高 4 分
- 总分：最高 8 分

钢片与横沟的区分：
- 横沟 (groove): 1.5-5mm（纵向厚度 ≥ groove_min_px）→ 分区锚点
- 钢片 (sipe):   0.4-0.8mm（sipe_min_px ≤ 厚度 < groove_min_px）→ 计数 + 位置评分
- 噪声:          < 0.4mm → 忽略
"""

import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from utils.logger import get_logger
from utils.exceptions import PatternDetectionError, ImageDimensionError
from configs.rules_config import HorizontalSipesConfig
from algorithms.detection.groove_intersection import _analyze_grooves

logger = get_logger("detect_horizontal_sipes")

# ============================================================
# 常量
# ============================================================

_DEFAULT_CFG = HorizontalSipesConfig()


# ============================================================
# 主函数
# ============================================================

def detect_horizontal_sipes(
    image: np.ndarray,
    image_type: str,
    sipe_width_mm: Optional[Dict[str, float]] = None,
    sipe_width_range_mm: Optional[List[float]] = None,
    groove_min_width_mm: Optional[Dict[str, float]] = None,
    pixel_per_mm: float = 7.1,
    sipe_count_max: Optional[Dict[str, int]] = None,
    position_tolerance: float = 0.3,
) -> Tuple[float, Dict[str, Any]]:
    """
    检测横向细线条（钢片）的数量和位置，并评分。

    Parameters
    ----------
    image : np.ndarray
        BGR 图像数组，期望尺寸 (128, 128, 3)。
    image_type : str
        小图类型，``"center"``（对应 RIB1/5）或 ``"side"``（对应 RIB2/3/4）。
    sipe_width_mm : dict, optional
        各类型 POC 阶段钢片宽度（mm），默认 ``{"center": 0.6, "side": 0.6}``。
    sipe_width_range_mm : list, optional
        钢片宽度范围 [min_mm, max_mm]，默认 ``[0.4, 0.8]``。
    groove_min_width_mm : dict, optional
        各类型横沟最小宽度（mm），用于分类锚点。
        默认 ``{"center": 3.5, "side": 1.8}``。
    pixel_per_mm : float
        图像像素密度（px/mm），默认 7.1。
    sipe_count_max : dict, optional
        各类型允许的最大钢片数。默认 ``{"center": 2, "side": 3}``。
    position_tolerance : float
        位置均分偏差容忍比例（0-1），默认 0.3。

    Returns
    -------
    score : float or None
        综合评分（需求9最高 4 分 + 需求10最高 4 分）。
        检测失败时返回 ``None``。
    details : dict
        成功时包含以下键：

        - ``rib_type`` (*str*)：RIB 类型
        - ``sipe_count`` (*int*)：检测到的钢片数量
        - ``sipe_positions`` (*list[float]*)：各钢片中心 Y 坐标（升序）
        - ``groove_count`` (*int*)：检测到的横沟数量（分区锚点）
        - ``groove_positions`` (*list[float]*)：各横沟中心 Y 坐标（升序）
        - ``is_valid`` (*bool*)：是否同时满足需求9与需求10
        - ``score_req9`` (*float*)：需求9得分
        - ``score_req10`` (*float*)：需求10得分
        - ``debug_image`` (*ndarray*)：BGR 标注图

        失败时仅包含：

        - ``err_msg`` (*str*)：错误描述
        - ``error_type`` (*str*)：异常类型名称
    """
    try:
        logger.debug("开始钢片检测，image_type=%s", image_type)

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
        rib_type = _DEFAULT_CFG.rib_label[image_type]
        img_h, img_w = image.shape[:2]

        # 横沟最小宽度（像素）— 用于分区锚点
        g_widths = groove_min_width_mm if groove_min_width_mm is not None else _DEFAULT_CFG.groove_min_width_mm
        groove_min_mm = g_widths.get(image_type, _DEFAULT_CFG.groove_min_width_mm[image_type])
        groove_min_px = max(1, int(round(groove_min_mm * pixel_per_mm)))

        # 钢片宽度范围（像素）
        s_range = sipe_width_range_mm if sipe_width_range_mm is not None else _DEFAULT_CFG.sipe_width_range_mm
        sipe_min_px = max(1, int(round(s_range[0] * pixel_per_mm)))
        sipe_max_px = max(sipe_min_px, int(round(s_range[1] * pixel_per_mm)))

        # 最大钢片数
        count_max_dict = sipe_count_max if sipe_count_max is not None else _DEFAULT_CFG.sipe_count_max
        max_count = count_max_dict.get(image_type, _DEFAULT_CFG.sipe_count_max[image_type])

        logger.debug(
            "rib_type=%s, groove_min_px=%d, sipe_px=[%d,%d], max_count=%d",
            rib_type, groove_min_px, sipe_min_px, sipe_max_px, max_count,
        )

        # ── Step 1: 灰度转换 + 高斯模糊降噪 ─────────────────────────
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # ── Step 2: 自适应二值化（暗色沟槽 → 白色前景）──────────────
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=31, C=5,
        )

        # ── Step 3: 横沟检测（复用 groove_intersection._analyze_grooves）
        groove_positions_raw, _, _ = _analyze_grooves(
            binary, groove_min_px, img_w,
        )
        logger.debug("横沟候选: count=%d, positions=%s",
                      len(groove_positions_raw), groove_positions_raw)

        # ── Step 3.5: 横沟验证 + 重分类（薄横沟 → 斜向钢片候选）──
        # 用大核 h-open 的行带厚度验证横沟：真横沟在 h-open 下仍保持
        # 较大厚度，而斜向钢片因角度原因厚度明显偏小
        h_kw_big = max(7, img_w // 8)
        h_kernel_big = cv2.getStructuringElement(cv2.MORPH_RECT, (h_kw_big, 1))
        binary_h_big = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel_big)

        groove_positions, reclassified_sipes = _verify_grooves(
            groove_positions_raw, binary_h_big, img_w,
            sipe_min_px, groove_min_px,
        )
        groove_count = len(groove_positions)
        logger.debug("横沟锚点: count=%d, positions=%s, 重分类=%s",
                      groove_count, groove_positions, reclassified_sipes)

        # ── Step 4a: 钢片检测 Pass 1（大核 h-open + 水平跨度过滤）──
        sipe_positions_p1, _ = _detect_sipes(
            binary_h_big, img_w, sipe_min_px, sipe_max_px, groove_min_px,
            min_span=img_w // 8,
        )
        logger.debug("Pass1 钢片: %s", sipe_positions_p1)

        # ── Step 4b: 钢片检测 Pass 2（小核 h-open，补充斜向钢片）──
        h_kw_small = 7
        h_kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (h_kw_small, 1))
        binary_h_small = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel_small)

        sipe_positions_p2, _ = _detect_sipes_pass2(
            binary_h_small, img_w, img_h,
            sipe_min_px, sipe_max_px, groove_min_px,
            groove_positions, sipe_positions_p1,
        )
        logger.debug("Pass2 钢片: %s", sipe_positions_p2)

        # ── Step 4c: Pass 3（CC 分析，检测大角度斜向钢片）──────────
        existing_p12 = sorted(sipe_positions_p1 + sipe_positions_p2
                              + reclassified_sipes)
        sipe_positions_p3, _ = _detect_sipes_pass3(
            binary_h_small, img_w, img_h,
            sipe_min_px, groove_min_px,
            groove_positions, existing_p12,
        )
        logger.debug("Pass3 钢片: %s", sipe_positions_p3)

        # ── Step 4d: 合并钢片（pass1 + pass2 + pass3 + 重分类，去重）
        all_sipes = sorted(existing_p12 + sipe_positions_p3)
        sipe_positions: List[float] = []
        for sp in all_sipes:
            if sipe_positions and abs(sp - sipe_positions[-1]) < 8:
                continue
            sipe_positions.append(sp)
        sipe_count = len(sipe_positions)
        logger.debug("钢片检测合计: count=%d, positions=%s", sipe_count, sipe_positions)

        # ── Step 5: 评分 ──────────────────────────────────────────────
        score_9 = _score_sipe_count(sipe_count, max_count)
        score_10 = _score_sipe_position(
            sipe_positions, groove_positions, img_h, position_tolerance,
        )
        score = float(score_9 + score_10)
        is_valid = (score_9 == _DEFAULT_CFG.score_sipe_count) and \
                   (score_10 == _DEFAULT_CFG.score_sipe_position)

        # ── Step 6: 生成调试标注图 ────────────────────────────────────
        debug_image = _draw_debug_image(
            image, groove_positions, sipe_positions,
            rib_type, sipe_count, score_9, score_10, score,
        )

        details: Dict[str, Any] = {
            "rib_type":         rib_type,
            "sipe_count":       sipe_count,
            "sipe_positions":   sipe_positions,
            "groove_count":     groove_count,
            "groove_positions": groove_positions,
            "is_valid":         is_valid,
            "score_req9":       float(score_9),
            "score_req10":      float(score_10),
            "debug_image":      debug_image,
        }
        logger.debug("钢片检测完成，score=%.1f, is_valid=%s", score, is_valid)
        return score, details

    except Exception as exc:
        err_msg = str(exc)
        error_type = type(exc).__name__
        logger.error("钢片检测失败：%s", err_msg)
        return None, {"err_msg": err_msg, "error_type": error_type}


# ============================================================
# 内部辅助函数
# ============================================================

def _verify_grooves(
    groove_positions: List[float],
    binary_h: np.ndarray,
    img_w: int,
    sipe_min_px: int,
    groove_min_px: int,
) -> Tuple[List[float], List[float]]:
    """
    验证横沟：用大核 h-open 的行带厚度区分真横沟和斜向钢片。

    真横沟在水平开运算后仍保持较大厚度，而斜向钢片因角度原因
    只保留极少行，带厚度明显偏小。

    Parameters
    ----------
    groove_positions : list[float]
        _analyze_grooves 返回的横沟候选中心坐标。
    binary_h : np.ndarray
        大核水平开运算后的二值图。
    img_w : int
        图像宽度。
    sipe_min_px : int
        钢片最小厚度（像素）。
    groove_min_px : int
        横沟最小厚度（像素）。

    Returns
    -------
    (verified_grooves, reclassified_sipes)
        verified_grooves    : list[float]  确认为横沟的位置
        reclassified_sipes  : list[float]  重分类为钢片候选的位置
    """
    if not groove_positions:
        return [], []

    row_sums = (binary_h > 0).sum(axis=1)
    min_px_per_row = max(sipe_min_px, img_w // 12)
    hot = np.where(row_sums >= min_px_per_row)[0]

    bands: List[List[int]] = []
    for r in hot.tolist():
        if bands and r - bands[-1][-1] <= 2:
            bands[-1].append(r)
        else:
            bands.append([r])

    max_thick = max((len(b) for b in bands), default=0)
    threshold = max(groove_min_px // 2, int(0.5 * max_thick)) \
        if max_thick > 0 else groove_min_px

    verified: List[float] = []
    reclassified: List[float] = []
    half_g = groove_min_px // 2
    for gp in groove_positions:
        gi = int(round(gp))
        # 查找 groove 附近的所有 h-open 带（允许 groove_min_px/2 距离）
        nearby = [
            b for b in bands
            if min(b) <= gi + half_g and max(b) >= gi - half_g
        ]
        thick = sum(len(b) for b in nearby)
        if thick >= threshold:
            verified.append(gp)
        else:
            reclassified.append(gp)

    return verified, reclassified


def _detect_sipes(
    binary: np.ndarray,
    img_w: int,
    sipe_min_px: int,
    sipe_max_px: int,
    groove_min_px: int,
    *,
    min_span: int = 0,
) -> Tuple[List[float], int]:
    """
    通过水平投影识别横向带状区域，按纵向厚度过滤出钢片。

    Parameters
    ----------
    binary : np.ndarray
        自适应二值化图像（暗色沟槽 = 白色前景）。
    img_w : int
        图像宽度（像素）。
    sipe_min_px : int
        钢片最小纵向厚度（像素）。
    sipe_max_px : int
        钢片最大纵向厚度（像素）。
    groove_min_px : int
        横沟最小纵向厚度（像素），用于排除横沟。
    min_span : int
        钢片最小水平跨度（像素），用于排除边缘噪声。

    Returns
    -------
    (positions, count)
        positions : list[float]  各钢片中心 Y 坐标（升序）
        count     : int          钢片数量
    """
    row_sums = (binary > 0).sum(axis=1)

    # 经过水平形态学开运算后，斜线/弯曲特征已被过滤
    # 使用较低的宽度门槛（1/12）以捕获短/细的水平钢片
    min_px_per_row = max(sipe_min_px, img_w // 12)

    hot = np.where(row_sums >= min_px_per_row)[0]

    # 合并连续行（允许最多 2 行空白）
    groups: List[List[int]] = []
    for r in hot.tolist():
        if groups and r - groups[-1][-1] <= 2:
            groups[-1].append(r)
        else:
            groups.append([r])

    # 按纵向厚度过滤：sipe_min_px ≤ thickness < groove_min_px
    # 使用较宽松的下限（max(1, sipe_min_px // 2)）以兼容亚像素级别的钢片
    effective_min = max(1, sipe_min_px // 2)
    sipe_groups = [
        g for g in groups
        if effective_min <= len(g) <= sipe_max_px and len(g) < groove_min_px
    ]

    # 可选：水平跨度过滤，排除仅出现在图像边缘的噪声
    if min_span > 0:
        filtered = []
        for g in sipe_groups:
            band_rows = binary[min(g):max(g) + 1]
            col_any = np.any(band_rows > 0, axis=0)
            if col_any.any():
                cols = np.where(col_any)[0]
                span = int(cols[-1] - cols[0] + 1)
                if span >= min_span:
                    filtered.append(g)
        sipe_groups = filtered

    positions = sorted(float(np.mean(g)) for g in sipe_groups)
    return positions, len(positions)


def _detect_sipes_pass2(
    binary: np.ndarray,
    img_w: int,
    img_h: int,
    sipe_min_px: int,
    sipe_max_px: int,
    groove_min_px: int,
    groove_positions: List[float],
    sipe_positions_p1: List[float],
    exclusion_radius: int = 8,
) -> Tuple[List[float], int]:
    """
    Pass 2 钢片检测：在小核 h-open 二值图上查找斜向钢片。

    排除横沟和 Pass 1 已检出钢片的附近区域，使用更严格的像素阈值
    以过滤弯曲花纹残留。

    Parameters
    ----------
    binary : np.ndarray
        小核 h-open 后的二值图。
    img_w, img_h : int
        图像宽度和高度。
    sipe_min_px, sipe_max_px, groove_min_px : int
        同 _detect_sipes。
    groove_positions : list[float]
        Pass 1 检出的横沟中心 Y 坐标。
    sipe_positions_p1 : list[float]
        Pass 1 检出的钢片中心 Y 坐标。
    exclusion_radius : int
        Pass 1 钢片附近的排除半径（行数）。

    Returns
    -------
    (positions, count)
    """
    row_sums = (binary > 0).sum(axis=1)

    # 构建排除区域：横沟 ± groove_min_px、Pass 1 钢片 ± exclusion_radius
    excluded: set = set()
    for gp in groove_positions:
        for r in range(max(0, int(gp) - groove_min_px), min(img_h, int(gp) + groove_min_px + 1)):
            excluded.add(r)
    for sp in sipe_positions_p1:
        for r in range(max(0, int(sp) - exclusion_radius), min(img_h, int(sp) + exclusion_radius + 1)):
            excluded.add(r)

    # 更严格的像素阈值（过滤弯曲花纹残留）
    min_px_per_row = max(13, img_w // 10)

    hot = [r for r in range(img_h) if row_sums[r] >= min_px_per_row and r not in excluded]

    groups: List[List[int]] = []
    for r in hot:
        if groups and r - groups[-1][-1] <= 2:
            groups[-1].append(r)
        else:
            groups.append([r])

    effective_min = max(1, sipe_min_px // 2)
    sipe_groups = [
        g for g in groups
        if effective_min <= len(g) <= sipe_max_px and len(g) < groove_min_px
    ]

    positions = sorted(float(np.mean(g)) for g in sipe_groups)
    return positions, len(positions)


def _detect_sipes_pass3(
    binary: np.ndarray,
    img_w: int,
    img_h: int,
    sipe_min_px: int,
    groove_min_px: int,
    groove_positions: List[float],
    existing_sipes: List[float],
    exclusion_radius: int = 10,
) -> Tuple[List[float], int]:
    """
    Pass 3 钢片检测：用连通域分析 + 最小外接矩形识别大角度斜向钢片。

    Pass 1/2 依赖行投影厚度过滤，对于角度较大（>15°）的斜向钢片，
    垂直投影厚度远大于实际线宽，导致被错误过滤。此 Pass 通过
    连通域的最小外接矩形测量真实线宽（minor axis）来识别。

    Parameters
    ----------
    binary : np.ndarray
        小核 h-open 后的二值图。
    img_w, img_h : int
        图像宽度和高度。
    sipe_min_px : int
        钢片最小纵向厚度（像素）。
    groove_min_px : int
        横沟最小纵向厚度（像素）。
    groove_positions : list[float]
        已确认的横沟中心 Y 坐标。
    existing_sipes : list[float]
        Pass 1/2 + 重分类已检出的钢片中心 Y 坐标。
    exclusion_radius : int
        已有钢片附近的排除半径（行数）。

    Returns
    -------
    (positions, count)
    """
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binary, connectivity=8,
    )

    min_major = max(15, img_w // 8)
    candidates: List[float] = []

    for i in range(1, n_labels):
        area = int(stats[i, cv2.CC_STAT_AREA])
        cy = float(centroids[i][1])

        if area < sipe_min_px * 3:
            continue
        # 排除图像边缘区域
        if cy < groove_min_px or cy > img_h - groove_min_px:
            continue
        # 排除已有横沟和钢片附近
        if any(abs(cy - gp) < groove_min_px for gp in groove_positions):
            continue
        if any(abs(cy - sp) < exclusion_radius for sp in existing_sipes):
            continue

        # 计算最小外接矩形
        mask_i = (labels == i).astype(np.uint8)
        contours, _ = cv2.findContours(
            mask_i, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
        )
        if not contours:
            continue
        rect = cv2.minAreaRect(contours[0])
        (_rx, _ry), (rw, rh), angle = rect
        minor = min(rw, rh)
        major = max(rw, rh)

        # 归一化角度到 [-90, 90) 范围（长轴方向）
        eff_angle = (angle + 90) if rw < rh else angle
        if eff_angle > 90:
            eff_angle -= 180
        if eff_angle < -90:
            eff_angle += 180

        # 过滤条件：
        # 1. 斜向（10°-40°）—— 近水平的应由 Pass 1/2 检出
        # 2. minor < groove_min_px（不是横沟）
        # 3. major 足够长（不是噪声）
        # 4. 足够细长（aspect ratio >= 2.5）
        if not (10 <= abs(eff_angle) <= 40):
            continue
        if minor >= groove_min_px:
            continue
        if major < min_major:
            continue
        if major / max(minor, 1) < 2.5:
            continue

        candidates.append(cy)

    # 去重
    candidates.sort()
    positions: List[float] = []
    for c in candidates:
        if positions and abs(c - positions[-1]) < 8:
            continue
        positions.append(c)

    return positions, len(positions)


def _score_sipe_count(sipe_count: int, max_count: int) -> int:
    """
    需求9评分：钢片数量是否在 [0, max_count] 范围内。

    二值制：在范围内得满分，否则 0 分。

    Parameters
    ----------
    sipe_count : int
        检测到的钢片数量。
    max_count : int
        允许的最大钢片数。

    Returns
    -------
    int
        得分（0 或 score_sipe_count 满分）。
    """
    if 0 <= sipe_count <= max_count:
        return _DEFAULT_CFG.score_sipe_count
    return 0


def _score_sipe_position(
    sipe_positions: List[float],
    groove_positions: List[float],
    img_h: int,
    tolerance: float,
) -> int:
    """
    需求10评分：钢片位置是否均分花纹块。

    花纹块由横沟和图像上下边缘界定。每个块内的钢片应均分块高度。
    所有块均满足 → 满分；任一不满足 → 0 分。
    0 根钢片 → 满分。

    Parameters
    ----------
    sipe_positions : list[float]
        各钢片中心 Y 坐标（升序）。
    groove_positions : list[float]
        各横沟中心 Y 坐标（升序），作为花纹块分区锚点。
    img_h : int
        图像高度（像素）。
    tolerance : float
        位置偏差容忍比例（偏差 ≤ 理想间距 × tolerance）。

    Returns
    -------
    int
        得分（0 或 score_sipe_position 满分）。
    """
    if len(sipe_positions) == 0:
        return _DEFAULT_CFG.score_sipe_position

    # 构建花纹块边界：[0, groove1, groove2, ..., img_h]
    boundaries = [0.0] + sorted(groove_positions) + [float(img_h)]

    # 将每根钢片归入花纹块
    blocks: Dict[int, List[float]] = {}
    for sp in sipe_positions:
        for i in range(len(boundaries) - 1):
            if boundaries[i] <= sp <= boundaries[i + 1]:
                blocks.setdefault(i, []).append(sp)
                break

    # 逐块检查均分
    for block_idx, block_sipes in blocks.items():
        block_top = boundaries[block_idx]
        block_bottom = boundaries[block_idx + 1]
        block_height = block_bottom - block_top

        if block_height <= 0:
            continue

        k = len(block_sipes)
        ideal_spacing = block_height / (k + 1)

        for j, sp in enumerate(sorted(block_sipes)):
            expected_y = block_top + ideal_spacing * (j + 1)
            deviation = abs(sp - expected_y)
            if deviation > ideal_spacing * tolerance:
                return 0

    return _DEFAULT_CFG.score_sipe_position


def _draw_debug_image(
    image: np.ndarray,
    groove_positions: List[float],
    sipe_positions: List[float],
    rib_type: str,
    sipe_count: int,
    score_9: int,
    score_10: int,
    score: float,
) -> np.ndarray:
    """
    在原图上叠加横沟和钢片标注，生成调试 BGR 图。

    - 绿色水平线：横沟位置（分区锚点）
    - 蓝色水平线：钢片位置
    - 左上角文字：RIB 类型、数量、评分
    """
    debug = image.copy()
    h, w = debug.shape[:2]

    # 横沟标注（绿色线）
    for y in groove_positions:
        cv2.line(debug, (0, int(round(y))), (w - 1, int(round(y))), (0, 200, 0), 2)

    # 钢片标注（蓝色线）
    for y in sipe_positions:
        cv2.line(debug, (0, int(round(y))), (w - 1, int(round(y))), (255, 128, 0), 1)

    # 文字标注（左上角）
    font = cv2.FONT_HERSHEY_SIMPLEX
    fscale = 0.35
    fthick = 1
    txt_color = (255, 255, 255)
    bg_color = (0, 0, 0)
    valid_9 = score_9 > 0
    valid_10 = score_10 > 0
    lines = [
        rib_type,
        f"Sipe:{sipe_count} {'OK' if valid_9 else 'NG'}",
        f"Pos:{'OK' if valid_10 else 'NG'}",
        f"S:{score:.0f}",
    ]
    y_cur = 10
    for line in lines:
        (tw, th), _ = cv2.getTextSize(line, font, fscale, fthick)
        cv2.rectangle(debug, (1, y_cur - th - 1), (3 + tw, y_cur + 2), bg_color, -1)
        cv2.putText(debug, line, (2, y_cur), font, fscale, txt_color, fthick, cv2.LINE_AA)
        y_cur += th + 4

    return debug
