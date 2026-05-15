# -*- coding: utf-8 -*-

"""
海陆比算法模块

计算轮胎花纹样稿的海陆比（黑色 + 灰色区域占总面积的百分比）。

算法层职责边界：
- 接收 np.ndarray 图像，返回海陆比数值和可选的可视化图像。
- 不保存文件，不接收 task_id 或输出路径，不含任何评分或业务配置逻辑。
- is_debug=True 时返回带颜色叠加标注的可视化图像，由调用方决定是否保存。
"""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.common.exceptions import InputDataError, RuntimeProcessError


logger = logging.getLogger(__name__)

_VIS_NAME = "land_sea_ratio"

# 像素亮度阈值（与老架构保持一致）
_BLACK_LOWER = 0
_BLACK_UPPER = 50
_GRAY_LOWER = 51
_GRAY_UPPER = 200


def compute_land_sea_ratio(
    image: np.ndarray,
    is_debug: bool = False,
) -> Tuple[float, str, Optional[np.ndarray]]:
    """
    计算轮胎花纹样稿的海陆比。

    Parameters
    ----------
    image : np.ndarray
        输入 BGR 图像，形状为 (H, W, 3)。
    is_debug : bool
        是否输出可视化调试图像，默认 False。

    Returns
    -------
    ratio_percent : float
        实际海陆比百分比，保留两位小数（如 30.52 表示 30.52%）。
    vis_name : str
        建议的可视化文件名（不含扩展名）；非 debug 模式返回空字符串。
    vis_image : Optional[np.ndarray]
        可视化图像（BGR）；非 debug 模式返回 None。

    Raises
    ------
    InputDataError
        image 为 None、非 ndarray 或非三通道 BGR 时抛出。
    RuntimeProcessError
        算法内部计算失败时抛出，原始异常挂在 __cause__ 上。
    """
    logger.debug("开始海陆比计算")

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

    logger.debug("海陆比结果: ratio=%.2f%%", ratio_percent)

    vis_name = ""
    vis_image = None
    if is_debug:
        try:
            vis_image = _draw_debug_image(image, gray, ratio_percent)
            vis_name = _VIS_NAME
        except Exception as original_error:
            raise RuntimeProcessError(
                "_draw_debug_image",
                "海陆比可视化处理失败",
                original_error,
            )

    return ratio_percent, vis_name, vis_image


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


def _draw_debug_image(
    image: np.ndarray,
    gray: np.ndarray,
    ratio_percent: float,
) -> np.ndarray:
    """
    生成可视化调试图：红色叠加黑色区域，绿色叠加灰色区域，左上角标注海陆比值。

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

    # 自适应字体大小（映射到 PIL 字号）
    height, width = vis.shape[:2]
    font_size = max(16, int(min(width, height) / 20))

    # 自适应文字颜色（根据左上角区域亮度）
    roi_h = max(1, min(100, height // 10))
    roi_w = max(1, min(200, width // 5))
    avg_brightness = float(np.mean(gray[:roi_h, :roi_w]))
    text_color = (0, 0, 0) if avg_brightness > 128 else (255, 255, 255)

    vis = _put_chinese_text(vis, f"海陆比：{ratio_percent:.2f}%", (10, 10), font_size, text_color)

    return vis


def _put_chinese_text(
    bgr_image: np.ndarray,
    text: str,
    position: tuple,
    font_size: int,
    color_bgr: tuple,
) -> np.ndarray:
    """用 PIL 在 BGR 图像上绘制中文文字，避免 cv2.putText 中文乱码。"""
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)
    draw = ImageDraw.Draw(pil_image)

    try:
        font = ImageFont.truetype("simhei.ttf", font_size)
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", font_size)
        except (IOError, OSError):
            font = ImageFont.load_default()

    # PIL 颜色为 RGB
    color_rgb = (color_bgr[2], color_bgr[1], color_bgr[0])
    draw.text(position, text, font=font, fill=color_rgb)

    result = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return result
