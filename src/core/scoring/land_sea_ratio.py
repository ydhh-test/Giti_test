# -*- coding: utf-8 -*-

"""
海陆比评分算法模块

计算轮胎花纹样稿的海陆比（黑色 + 灰色区域占总面积的百分比），并按三级容差规则给出评分。

算法层职责边界：
- 接收 np.ndarray 图像，返回显式的评分结果和可选的可视化图像。
- 不保存文件，不接收 task_id 或输出路径，不计算规则得分以外的业务逻辑。
- is_debug=True 时返回带颜色叠加标注的可视化图像，由调用方决定是否保存。
"""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

from src.common.exceptions import InputDataError, RuntimeProcessError


logger = logging.getLogger(__name__)

_VIS_NAME = "land_sea_ratio.png"

# 像素亮度阈值（与老架构保持一致）
_BLACK_LOWER = 0
_BLACK_UPPER = 50
_GRAY_LOWER = 51
_GRAY_UPPER = 200


def compute_land_sea_ratio(
    image: np.ndarray,
    target_min: float = 28.0,
    target_max: float = 35.0,
    margin: float = 5.0,
    is_debug: bool = False,
) -> Tuple[int, float, str, Optional[np.ndarray]]:
    """
    计算轮胎花纹样稿的海陆比，并按三级容差规则给出评分。

    Parameters
    ----------
    image : np.ndarray
        输入 BGR 图像，形状为 (H, W, 3)。
    target_min : float
        海陆比目标区间下界（百分比，默认 28.0）。
    target_max : float
        海陆比目标区间上界（百分比，默认 35.0）。
    margin : float
        容差宽度（百分比，默认 5.0）。落在 [target_min-margin, target_min) 或
        (target_max, target_max+margin] 内得 1 分；超出得 0 分。
    is_debug : bool
        是否输出可视化调试图像，默认 False。

    Returns
    -------
    score : int
        评分结果：2（优秀）、1（合格）、0（不合格）。
    ratio_percent : float
        实际海陆比百分比，保留两位小数（如 30.52 表示 30.52%）。
    vis_name : str
        建议的可视化文件名；非 debug 模式返回空字符串。
    vis_image : Optional[np.ndarray]
        可视化图像（BGR）；非 debug 模式返回 None。

    Raises
    ------
    InputDataError
        image 为 None、非 ndarray、非三通道 BGR，或评分参数不合法时抛出。
    RuntimeProcessError
        算法内部计算失败时抛出，原始异常挂在 __cause__ 上。

    Notes
    -----
    算法层不计算规则得分以外的业务逻辑，不保存文件，不接收 task_id 或输出路径。
    """
    logger.debug(
        "开始海陆比计算，target_min=%.1f, target_max=%.1f, margin=%.1f",
        target_min,
        target_max,
        margin,
    )

    if image is None:
        raise InputDataError("image", "value", "must not be None")

    if not isinstance(image, np.ndarray):
        raise InputDataError(
            "image", "type", "expected np.ndarray", type(image).__name__
        )

    if image.ndim != 3 or image.shape[2] != 3:
        raise InputDataError(
            "image", "shape", "expected (H, W, 3) BGR image", image.shape
        )

    if not isinstance(target_min, (int, float)) or target_min < 0:
        raise InputDataError(
            "target_min", "value", "must be a non-negative number", target_min
        )

    if not isinstance(target_max, (int, float)) or target_max <= target_min:
        raise InputDataError(
            "target_max", "value", "must be > target_min", target_max
        )

    if not isinstance(margin, (int, float)) or margin < 0:
        raise InputDataError(
            "margin", "value", "must be a non-negative number", margin
        )

    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        total_area = image.shape[0] * image.shape[1]

        black_area = _compute_black_area(gray)
        gray_area = _compute_gray_area(gray)

        ratio_percent = round((black_area + gray_area) / total_area * 100, 2) if total_area > 0 else 0.0

        logger.debug(
            "海陆比计算明细: ratio=%.2f%%, black=%d, gray=%d, total=%d",
            ratio_percent,
            black_area,
            gray_area,
            total_area,
        )

    except Exception as original_error:
        raise RuntimeProcessError(
            "compute_land_sea_ratio",
            "海陆比面积计算失败",
            original_error,
        )

    score = _score(ratio_percent, target_min, target_max, margin)

    logger.debug(
        "海陆比评分结果: ratio=%.2f%%, score=%d",
        ratio_percent,
        score,
    )

    vis_name = ""
    vis_image = None
    if is_debug:
        try:
            vis_image = _draw_debug_image(image, gray, ratio_percent, score)
            vis_name = _VIS_NAME
        except Exception as original_error:
            raise RuntimeProcessError(
                "_draw_debug_image",
                "海陆比可视化处理失败",
                original_error,
            )

    return score, ratio_percent, vis_name, vis_image


# ------------------------------------------------------------------
# 内部辅助函数
# ------------------------------------------------------------------

def _compute_black_area(gray: np.ndarray) -> int:
    """统计黑色区域像素数（灰度值在 [0, 50] 范围内）。"""
    mask = cv2.inRange(gray, _BLACK_LOWER, _BLACK_UPPER)
    return int(cv2.countNonZero(mask))


def _compute_gray_area(gray: np.ndarray) -> int:
    """统计灰色区域像素数（灰度值在 [51, 200] 范围内）。"""
    mask = cv2.inRange(gray, _GRAY_LOWER, _GRAY_UPPER)
    return int(cv2.countNonZero(mask))


def _score(ratio_percent: float, target_min: float, target_max: float, margin: float) -> int:
    """根据三级容差规则计算评分。"""
    if target_min <= ratio_percent <= target_max:
        return 2
    lower_margin = target_min - margin
    upper_margin = target_max + margin
    if lower_margin <= ratio_percent < target_min or target_max < ratio_percent <= upper_margin:
        return 1
    return 0


def _draw_debug_image(
    image: np.ndarray,
    gray: np.ndarray,
    ratio_percent: float,
    score: int,
) -> np.ndarray:
    """
    生成可视化调试图：红色叠加黑色区域，绿色叠加灰色区域，左上角标注比值和评分。

    与老架构 rule13.visualize_score() 保持逐像素等价。
    """
    vis = image.copy()

    black_mask = cv2.inRange(gray, _BLACK_LOWER, _BLACK_UPPER)
    gray_mask = cv2.inRange(gray, _GRAY_LOWER, _GRAY_UPPER)

    # 红色叠加黑色区域（BGR: 0, 0, 255）
    red_overlay = np.zeros_like(vis)
    red_overlay[:, :] = (0, 0, 255)
    red_masked = cv2.bitwise_and(red_overlay, red_overlay, mask=black_mask)
    vis = cv2.addWeighted(vis, 1.0, red_masked, 0.5, 0)

    # 绿色叠加灰色区域（BGR: 0, 255, 0）
    green_overlay = np.zeros_like(vis)
    green_overlay[:, :] = (0, 255, 0)
    green_masked = cv2.bitwise_and(green_overlay, green_overlay, mask=gray_mask)
    vis = cv2.addWeighted(vis, 1.0, green_masked, 0.5, 0)

    # 自适应字体大小
    height, width = vis.shape[:2]
    font_scale = min(width, height) / 500
    font_scale = max(0.5, min(2.0, font_scale))

    # 自适应文字颜色（根据左上角区域亮度）
    roi_h = max(1, min(100, height // 10))
    roi_w = max(1, min(200, width // 5))
    avg_brightness = float(np.mean(gray[:roi_h, :roi_w]))
    text_color = (0, 0, 0) if avg_brightness > 128 else (255, 255, 255)

    y_offset = int(30 * font_scale)
    thickness = max(1, int(2 * font_scale))

    cv2.putText(
        vis,
        f"海陆比：{ratio_percent:.2f}%",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        text_color,
        thickness,
    )
    cv2.putText(
        vis,
        f"评分：{score}",
        (10, int(y_offset * 2.5)),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        text_color,
        thickness,
    )

    return vis
