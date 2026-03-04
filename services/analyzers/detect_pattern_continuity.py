# -*- coding: utf-8 -*-

"""
图案连续性检测模块

检测灰度图中上下边缘的线条是否连续对齐，为后续的上下循环拼接服务。
"""

# Copyright © 2026 云端辉鸿. All rights reserved.
# Author: 桂禹 <guiyu@cloudhuihong.com>
# AI Assistant: ClaudeCode (Claude Sonnet 4)

import cv2
import numpy as np
from itertools import product
from typing import Tuple, Dict, Any, List, Optional

from configs.rules_config import PatternContinuityConfig


def detect_pattern_continuity(
    image: np.ndarray,
    conf: Dict[str, Any],
    *args,
    **kwargs
) -> Tuple[int, Dict[str, Any]]:
    """
    检测图案上下边缘的连续性

    Parameters:
    - image: 输入灰度图 (H, W)
    - conf: 配置字典，包含评分规则和参数
    - *args, **kwargs: 额外参数（method='A'或'B', visualize=True等）

    Returns:
    - score: 评分（连续返回conf['score']，不连续返回0）
    - details: 详细信息字典

    details 包含:
    {
        'is_continuous': bool,
        'top_ends': List[Tuple[int, int, str]],
        'bottom_ends': List[Tuple[int, int, str]],
        'matches': List[Tuple[int, int]],
        'unmatched_top': List[int],
        'unmatched_bottom': List[int],
        'visualization': Optional[np.ndarray]
    }
    """
    # 创建配置对象
    config = PatternContinuityConfig.from_dict(conf)

    # 获取额外参数
    method = kwargs.get('method', 'A')
    visualize = kwargs.get('visualize', False)

    # 提取边缘端点
    if method.upper() == 'A':
        top_ends, bottom_ends = _detect_with_method_a(image, config)
    elif method.upper() == 'B':
        top_ends, bottom_ends = _detect_with_method_b(image, config)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'A' or 'B'")

    # 匹配端点
    matches, unmatched_top, unmatched_bottom = _match_ends(top_ends, bottom_ends, config)

    # 判定连续性
    is_continuous = len(unmatched_bottom) == 0

    # 计算评分
    score = config.score if is_continuous else 0

    # 构建详细信息
    details = {
        'is_continuous': is_continuous,
        'top_ends': top_ends,
        'bottom_ends': bottom_ends,
        'matches': matches,
        'unmatched_top': unmatched_top,
        'unmatched_bottom': unmatched_bottom,
        'visualization': None
    }

    # 可视化
    if visualize:
        details['visualization'] = _visualize_detection(
            image, top_ends, bottom_ends, matches,
            unmatched_top, unmatched_bottom, config
        )

    return score, details


def get_adaptive_threshold(image: np.ndarray, config: PatternContinuityConfig) -> int:
    """
    计算自适应阈值

    Parameters:
    - image: 输入灰度图
    - config: 配置对象

    Returns:
    - threshold: 计算得到的阈值
    """
    if config.adaptive_method == 'otsu':
        # 使用Otsu算法
        threshold, _ = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return int(threshold)
    elif config.adaptive_method == 'adaptive':
        # 使用中位数或平均值
        return int(np.median(image))
    else:
        raise ValueError(f"Unknown adaptive_method: {config.adaptive_method}")


def _detect_with_method_a(
    image: np.ndarray,
    config: PatternContinuityConfig
) -> Tuple[List[Tuple[int, int, str]], List[Tuple[int, int, str]]]:
    """
    使用方法A（纯像素操作）检测边缘端点

    Parameters:
    - image: 输入灰度图
    - config: 配置对象

    Returns:
    - top_ends: 上边缘端点列表 [(min_x, max_x, type), ...]
    - bottom_ends: 下边缘端点列表 [(min_x, max_x, type), ...]
    """
    # 计算阈值
    if config.use_adaptive_threshold:
        threshold = get_adaptive_threshold(image, config)
    else:
        threshold = config.threshold

    # 提取上边缘端点
    top_region = image[0:config.edge_height, :]
    top_ends = _extract_ends_from_region(top_region, threshold, config, is_top=True)

    # 提取下边缘端点
    bottom_region = image[-config.edge_height:, :]
    bottom_ends = _extract_ends_from_region(bottom_region, threshold, config, is_top=False)

    return top_ends, bottom_ends


def _extract_ends_from_region(
    region: np.ndarray,
    threshold: int,
    config: PatternContinuityConfig,
    is_top: bool
) -> List[Tuple[int, int, str]]:
    """
    从边缘区域提取端点

    Parameters:
    - region: 边缘区域图像
    - threshold: 灰度阈值
    - config: 配置对象
    - is_top: 是否为上边缘

    Returns:
    - ends: 端点列表 [(min_x, max_x, type), ...]
    """
    # 确定检查的行
    if is_top:
        row = region[0, :]  # 上边缘检查第一行
    else:
        row = region[-1, :]  # 下边缘检查最后一行

    # 二值化
    binary = row <= threshold

    # 找到深色连通区间
    ends = []
    i = 0
    while i < len(binary):
        if binary[i]:  # 找到深色像素
            start_x = i
            # 找到区间结束位置
            while i < len(binary) and binary[i]:
                i += 1
            end_x = i - 1

            # 计算宽度
            width = end_x - start_x + 1

            # 过滤噪音
            if width >= config.min_line_width:
                # 判断粗细
                line_type = 'coarse' if width >= config.coarse_threshold else 'fine'

                # 粗线使用区间，细线使用中心点
                if line_type == 'fine':
                    center_x = (start_x + end_x) // 2
                    ends.append((center_x, center_x, 'fine'))
                else:
                    ends.append((start_x, end_x, 'coarse'))
        else:
            i += 1

    return ends


def _detect_with_method_b(
    image: np.ndarray,
    config: PatternContinuityConfig
) -> Tuple[List[Tuple[int, int, str]], List[Tuple[int, int, str]]]:
    """
    使用方法B（OpenCV轮廓检测）检测边缘端点

    Parameters:
    - image: 输入灰度图
    - config: 配置对象

    Returns:
    - top_ends: 上边缘端点列表 [(min_x, max_x, type), ...]
    - bottom_ends: 下边缘端点列表 [(min_x, max_x, type), ...]
    """
    # 计算阈值
    if config.use_adaptive_threshold:
        threshold = get_adaptive_threshold(image, config)
    else:
        threshold = config.threshold

    # 二值化
    _, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY_INV)

    # 提取上边缘端点
    top_region = binary[0:config.edge_height, :]
    top_ends = _extract_ends_from_contours(top_region, config)

    # 提取下边缘端点
    bottom_region = binary[-config.edge_height:, :]
    bottom_ends = _extract_ends_from_contours(bottom_region, config)

    return top_ends, bottom_ends


def _extract_ends_from_contours(
    region: np.ndarray,
    config: PatternContinuityConfig
) -> List[Tuple[int, int, str]]:
    """
    从轮廓提取端点

    Parameters:
    - region: 边缘区域图像（二值）
    - config: 配置对象

    Returns:
    - ends: 端点列表 [(min_x, max_x, type), ...]
    """
    # 查找轮廓
    contours, _ = cv2.findContours(
        region,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    ends = []
    for contour in contours:
        # 获取边界框
        x, y, w, h = cv2.boundingRect(contour)

        # 过滤噪音
        if w < config.min_line_width:
            continue

        # 判断粗细
        line_type = 'coarse' if w >= config.coarse_threshold else 'fine'

        # 粗线使用区间，细线使用中心点
        if line_type == 'fine':
            center_x = x + w // 2
            ends.append((center_x, center_x, 'fine'))
        else:
            ends.append((x, x + w - 1, 'coarse'))

    return ends


def _match_ends(
    top_ends: List[Tuple[int, int, str]],
    bottom_ends: List[Tuple[int, int, str]],
    config: PatternContinuityConfig
) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    """
    匹配上下边缘端点

    Parameters:
    - top_ends: 上边缘端点列表
    - bottom_ends: 下边缘端点列表
    - config: 配置对象

    Returns:
    - matches: 匹配对列表 [(top_idx, bottom_idx), ...]
    - unmatched_top: 未匹配的上边缘索引列表
    - unmatched_bottom: 未匹配的下边缘索引列表
    """
    # 初始化
    unmatched_bottom = set(range(len(bottom_ends)))
    matches = []

    # 全排列匹配
    for top_idx, bottom_idx in product(range(len(top_ends)), range(len(bottom_ends))):
        if bottom_idx in unmatched_bottom:
            if _can_match(top_ends[top_idx], bottom_ends[bottom_idx], config):
                unmatched_bottom.remove(bottom_idx)
                matches.append((top_idx, bottom_idx))

    # 找出未匹配的上边缘
    matched_top = {top_idx for top_idx, _ in matches}
    unmatched_top = [i for i in range(len(top_ends)) if i not in matched_top]

    return matches, unmatched_top, list(unmatched_bottom)


def _can_match(
    top_end: Tuple[int, int, str],
    bottom_end: Tuple[int, int, str],
    config: PatternContinuityConfig
) -> bool:
    """
    判断两个端点是否可以匹配

    Parameters:
    - top_end: 上边缘端点 (min_x, max_x, type)
    - bottom_end: 下边缘端点 (min_x, max_x, type)
    - config: 配置对象

    Returns:
    - can_match: 是否可以匹配
    """
    top_min_x, top_max_x, top_type = top_end
    bottom_min_x, bottom_max_x, bottom_type = bottom_end

    # 细线-细线匹配
    if top_type == 'fine' and bottom_type == 'fine':
        distance = abs(top_min_x - bottom_min_x)
        return distance <= config.fine_match_distance

    # 细线-粗线匹配
    if top_type == 'fine' and bottom_type == 'coarse':
        return bottom_min_x <= top_min_x <= bottom_max_x

    # 粗线-细线匹配
    if top_type == 'coarse' and bottom_type == 'fine':
        return top_min_x <= bottom_min_x <= top_max_x

    # 粗线-粗线匹配
    if top_type == 'coarse' and bottom_type == 'coarse':
        # 计算重合长度
        overlap_start = max(top_min_x, bottom_min_x)
        overlap_end = min(top_max_x, bottom_max_x)
        overlap_length = overlap_end - overlap_start + 1

        # 计算较短区间长度
        top_length = top_max_x - top_min_x + 1
        bottom_length = bottom_max_x - bottom_min_x + 1
        shorter_length = min(top_length, bottom_length)

        # 计算重合比例
        if shorter_length == 0:
            return False
        overlap_ratio = overlap_length / shorter_length

        return overlap_ratio >= config.coarse_overlap_ratio

    return False


def _visualize_detection(
    image: np.ndarray,
    top_ends: List[Tuple[int, int, str]],
    bottom_ends: List[Tuple[int, int, str]],
    matches: List[Tuple[int, int]],
    unmatched_top: List[int],
    unmatched_bottom: List[int],
    config: PatternContinuityConfig
) -> np.ndarray:
    """
    可视化检测结果

    Parameters:
    - image: 原始图像
    - top_ends: 上边缘端点列表
    - bottom_ends: 下边缘端点列表
    - matches: 匹配对列表
    - unmatched_top: 未匹配的上边缘索引
    - unmatched_bottom: 未匹配的下边缘索引
    - config: 配置对象

    Returns:
    - visualization: 可视化图像（RGB）
    """
    # 转换为RGB
    vis = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

    # 生成颜色
    colors = _generate_colors(len(top_ends) + len(bottom_ends))

    # 绘制上边缘端点
    for i, (min_x, max_x, line_type) in enumerate(top_ends):
        color = colors[i]
        is_unmatched = i in unmatched_top

        if is_unmatched:
            # 未匹配用黄色高亮
            color = (0, 255, 255)

        if line_type == 'fine':
            # 细线画圆点
            center_x = min_x
            cv2.circle(vis, (center_x, 0), config.vis_line_width * 2, color, -1)
        else:
            # 粗线画矩形
            cv2.rectangle(vis, (min_x, 0), (max_x, 3), color, config.vis_line_width)

    # 绘制下边缘端点
    h = image.shape[0]
    for i, (min_x, max_x, line_type) in enumerate(bottom_ends):
        color = colors[len(top_ends) + i]
        is_unmatched = i in unmatched_bottom

        if is_unmatched:
            # 未匹配用黄色高亮
            color = (0, 255, 255)

        if line_type == 'fine':
            # 细线画圆点
            center_x = min_x
            cv2.circle(vis, (center_x, h - 1), config.vis_line_width * 2, color, -1)
        else:
            # 粗线画矩形
            cv2.rectangle(vis, (min_x, h - 4), (max_x, h - 1), color, config.vis_line_width)

    # 绘制匹配连线
    for top_idx, bottom_idx in matches:
        top_min_x, top_max_x, top_type = top_ends[top_idx]
        bottom_min_x, bottom_max_x, bottom_type = bottom_ends[bottom_idx]

        # 计算起点和终点
        if top_type == 'fine':
            start_x = top_min_x
        else:
            start_x = (top_min_x + top_max_x) // 2

        if bottom_type == 'fine':
            end_x = bottom_min_x
        else:
            end_x = (bottom_min_x + bottom_max_x) // 2

        # 绘制绿色连线
        cv2.line(vis, (start_x, 0), (end_x, h - 1), (0, 255, 0), config.vis_line_width)

    # 标记边缘区域
    cv2.line(vis, (0, config.edge_height), (image.shape[1] - 1, config.edge_height), (255, 0, 0), 1)
    cv2.line(vis, (0, h - config.edge_height), (image.shape[1] - 1, h - config.edge_height), (255, 0, 0), 1)

    return vis


def _generate_colors(n: int) -> List[Tuple[int, int, int]]:
    """
    生成n种不同的颜色

    Parameters:
    - n: 需要的颜色数量

    Returns:
    - colors: 颜色列表 [(R, G, B), ...]
    """
    colors = []
    for i in range(n):
        hue = int(180 * i / n)  # 使用HSV颜色轮
        color = cv2.cvtColor(np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2RGB)[0, 0]
        colors.append(tuple(map(int, color)))
    return colors
