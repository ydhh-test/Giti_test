# -*- coding: utf-8 -*-

"""
裁剪、切分、边缘清理
图像的"切分"动作——纵向分割（去黑沟）、边缘清理（去白边/灰边）、横向分割（周期检测/随机裁剪）
"""

# Copyright © 2026. All rights reserved.

import cv2
import numpy as np
import random

from src.utils.logger import get_logger

logger = get_logger(__name__)


def remove_black_and_split_segments(image, num_segments_to_remove=4):
    """
    删除图像中连续全黑列中宽度最大的num_segments_to_remove段，
    返回剩余连续列段的独立图片列表

    Args:
        image: numpy数组 (BGR格式)
        num_segments_to_remove: 要移除的黑色段数量，支持3或4

    Returns:
        list[numpy.ndarray]: 分割后的图像列表
            - num_segments_to_remove=4 时，返回5张图像
            - num_segments_to_remove=3 时，返回4张图像
    """
    if num_segments_to_remove not in [3, 4]:
        raise ValueError(f"num_segments_to_remove只支持3或4，当前值为{num_segments_to_remove}")

    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w, c = img_rgb.shape

    dark_pixels = np.all(img_rgb < 10, axis=2)
    black_mask = (dark_pixels.sum(axis=0) / h) > 0.95

    segments = []
    start = None
    for i in range(w):
        if black_mask[i]:
            if start is None:
                start = i
        else:
            if start is not None:
                segments.append((start, i-1))
                start = None
    if start is not None:
        segments.append((start, w-1))

    segments = [(s, e) for s, e in segments if (e - s + 1) >= 5]

    if len(segments) >= num_segments_to_remove:
        segments_sorted = sorted(segments, key=lambda x: x[1]-x[0]+1, reverse=True)
        segments_to_remove = segments_sorted[:num_segments_to_remove]
    else:
        logger.warning(f"只检测到 {len(segments)} 个黑色段，少于需要的 {num_segments_to_remove} 个")
        segments_to_remove = segments

    keep_mask = np.ones(w, dtype=bool)
    for s, e in segments_to_remove:
        keep_mask[s:e+1] = False

    remaining_segments = []
    start = None
    for i in range(w):
        if keep_mask[i]:
            if start is None:
                start = i
        else:
            if start is not None:
                remaining_segments.append((start, i-1))
                start = None
    if start is not None:
        remaining_segments.append((start, w-1))

    parts = []
    for idx, (s, e) in enumerate(remaining_segments):
        part_img = img_rgb[:, s:e+1, :]
        part_bgr = cv2.cvtColor(part_img, cv2.COLOR_RGB2BGR)
        parts.append(part_bgr)

    return parts


def remove_side_white(image, direction='left'):
    """
    去除图像单侧的白色边缘

    Args:
        image: numpy数组 (BGR格式)
        direction: 'left' 或 'right'，表示要去除哪一侧的白边

    Returns:
        裁剪后的图像
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
    height, width = thresh.shape[:2]

    if direction == 'right':
        right_bound = width - 1
        for col in range(width-1, -1, -1):
            col_sum = thresh[:, col].sum()
            if col_sum < height * 255:
                right_bound = col
                break
        return image[:, :right_bound + 1]
    else:
        left_bound = 0
        for col in range(width):
            col_sum = thresh[:, col].sum()
            if col_sum < height * 255:
                left_bound = col
                break
        return image[:, left_bound:]


def remove_edge_gray(image, target_gray=(137,137,137),
                     tolerance=90, edge_percent=23):
    """
    将图片左右边缘的特定灰色背景替换为白色

    Args:
        image: numpy数组 (BGR格式)
        target_gray: 目标灰色BGR值
        tolerance: 容差
        edge_percent: 边缘宽度百分比

    Returns:
        numpy数组: 处理后的BGR图像
    """
    img_cv = image.copy()

    height, width = img_cv.shape[:2]
    result = img_cv.copy()

    edge_width = int(width * edge_percent / 100)

    target = np.array(target_gray)
    lower_bound = np.clip(target - tolerance, 0, 255)
    upper_bound = np.clip(target + tolerance, 0, 255)

    left_edge = result[:, :edge_width]
    mask_left = np.all((left_edge > lower_bound) & (left_edge < upper_bound), axis=2)
    left_edge[mask_left] = [255, 255, 255]

    right_edge = result[:, -edge_width:]
    mask_right = np.all((right_edge > lower_bound) & (right_edge < upper_bound), axis=2)
    right_edge[mask_right] = [255, 255, 255]

    return result


def random_horizontal_crop(image, min_splits=5, max_splits=7):
    """
    随机水平裁剪图像的一部分

    Args:
        image: numpy数组 (BGR格式)
        min_splits: 最小分割数
        max_splits: 最大分割数

    Returns:
        裁剪后的图像块
    """
    img = image.copy()

    h, w = img.shape[:2]
    split_count = random.randint(min_splits, max_splits)

    base_height = h // split_count
    block_height = base_height + 1

    max_start = max(1, h - block_height)
    current_y = random.randint(0, max_start)
    end_y = min(current_y + block_height, h)

    return img[current_y:end_y, :, :]


def detect_periodic_blocks(image, min_cycles=5, max_cycles=7, min_block_pixels=100):
    """
    检测图像中的周期性色块并返回第一个有效周期块

    Args:
        image: numpy数组 (BGR格式)
        min_cycles: 最小周期数
        max_cycles: 最大周期数
        min_block_pixels: 最小有效像素数

    Returns:
        numpy数组或None
    """
    img = image.copy()

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    row_density = np.sum(binary, axis=1) / w
    row_density = row_density.astype(np.float32)
    row_density -= np.mean(row_density)

    autocorr = np.correlate(row_density, row_density, mode='full')
    autocorr = autocorr[len(autocorr)//2:]

    min_period = h // max_cycles
    max_period = h // min_cycles
    peak_threshold = 0.3 * np.max(autocorr)

    peak_lags = []
    for lag in range(min_period, min(max_period, len(autocorr)-1)):
        if (autocorr[lag] > autocorr[lag-1] and
            autocorr[lag] > autocorr[lag+1] and
            autocorr[lag] > peak_threshold):
            peak_lags.append(lag)

    if not peak_lags:
        return None

    period = int(np.median(peak_lags))
    cycle_count = h // period

    if not (min_cycles <= cycle_count <= max_cycles):
        logger.debug(f"周期数{cycle_count}不在范围内[{min_cycles}-{max_cycles}]")
        return None

    for i in range(cycle_count):
        start_y = i * period
        end_y = min((i + 1) * period, h)
        cycle_block = img[start_y:end_y, :, :]

        cycle_gray = cv2.cvtColor(cycle_block, cv2.COLOR_BGR2GRAY)
        _, cycle_binary = cv2.threshold(cycle_gray, 200, 255, cv2.THRESH_BINARY_INV)

        if np.sum(cycle_binary) > min_block_pixels:
            logger.debug(f"找到周期性色块，周期数={cycle_count}")
            return cycle_block

    return None
