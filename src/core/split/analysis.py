# -*- coding: utf-8 -*-

"""图像分析与质量检测"""

# Copyright © 2026. All rights reserved.

import cv2
import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)


def analyze_dominant_color(image, lower_bound=15, upper_bound=240, default_color=(137,137,137)):
    """
    分析图像主色调，返回在指定范围内的主要颜色

    Args:
        image: numpy数组 (BGR格式)
        lower_bound: 颜色下限
        upper_bound: 颜色上限
        default_color: 默认颜色

    Returns:
        tuple: (R, G, B)
    """
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if image.shape[2] == 3 else image

    pixels = img_rgb.reshape(-1, 3)
    unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
    top_colors = unique_colors[np.argsort(-counts)[:10]]

    for color in top_colors:
        if np.all((color >= lower_bound) & (color <= upper_bound)):
            return tuple(color)

    return default_color


def remove_vertical_lines_center(image, x_tolerance=2, length_ratio=0.7,
                                 line_width=2, margin_ratio=0.1,
                                 hough_threshold=50, min_line_gap=10):
    """
    检测图像中央区域的竖直线并去除，保护与其他线段的交点

    Args:
        image: numpy数组 (BGR格式)
        x_tolerance: X轴容差
        length_ratio: 最小线长比例
        line_width: 线条宽度
        margin_ratio: 边缘比例
        hough_threshold: Hough变换阈值
        min_line_gap: 最小线间距

    Returns:
        numpy数组或None: 处理后的图像，如果未检测到竖直线则返回None
    """
    img = image.copy()

    height, width = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    min_line_length = int(height * length_ratio)
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180,
                           threshold=hough_threshold,
                           minLineLength=min_line_length,
                           maxLineGap=min_line_gap)

    if lines is None:
        return None

    left_bound = int(width * margin_ratio)
    right_bound = int(width * (1 - margin_ratio))

    vertical_mask = np.zeros((height, width), dtype=np.uint8)
    other_mask = np.zeros((height, width), dtype=np.uint8)

    for line in lines:
        x1, y1, x2, y2 = line[0]
        if y1 > y2:
            x1, y1, x2, y2 = x2, y2, x1, y1

        is_vertical = abs(x1 - x2) <= x_tolerance
        x_min, x_max = min(x1, x2), max(x1, x2)
        in_center = (x_min >= left_bound) and (x_max <= right_bound)

        if is_vertical and in_center:
            cv2.line(vertical_mask, (x1, y1), (x2, y2), 255, line_width)
        else:
            cv2.line(other_mask, (x1, y1), (x2, y2), 255, line_width)

    if not np.any(vertical_mask):
        return None

    intersection = cv2.bitwise_and(vertical_mask, other_mask)
    kernel = np.ones((3,3), np.uint8)
    intersection_dilated = cv2.dilate(intersection, kernel)
    vertical_mask_clean = cv2.bitwise_and(vertical_mask, cv2.bitwise_not(intersection_dilated))

    result = img.copy()
    result[vertical_mask_clean > 0] = [255, 255, 255]

    return result


def analyze_single_image_abnormalities(image):
    """
    分析单张图片的异常情况

    Args:
        image: numpy数组 (BGR格式)

    Returns:
        tuple: (is_abnormal: bool, abnormalities: list[str])
            - is_abnormal: 是否存在异常
            - abnormalities: 异常描述列表，如 ["宽高比异常(宽/高=5.23>4)", "颜色种类过少(2<3)"]
    """
    abnormalities = []

    height, width = image.shape[:2]

    if height > 0 and width / height > 4:
        abnormalities.append(f"宽高比异常(宽/高={width/height:.2f}>4)")
    elif width > 0 and height / width > 4:
        abnormalities.append(f"宽高比异常(高/宽={height/width:.2f}>4)")

    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pixels = img_rgb.reshape(-1, 3)
    unique_colors = len(set(map(tuple, pixels)))

    if unique_colors < 3:
        abnormalities.append(f"颜色种类过少({unique_colors}<3)")

    return (len(abnormalities) > 0, abnormalities)
