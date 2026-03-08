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
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional

from configs.rules_config import PatternContinuityConfig
from utils.logger import get_logger
from utils.exceptions import (
    PatternDetectionError,
    ContinuityAnalysisError,
    ImageDimensionError,
    ImageSaveError
)

# 创建模块级日志记录器
logger = get_logger("detect_pattern_continuity")


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
    - *args, **kwargs: 额外参数
        - method: 检测方法，'A'（纯像素操作）或'B'（OpenCV轮廓检测），默认'B'
        - visualize: 是否生成可视化，默认True
        - task_id: 任务ID，用于保存可视化图片，格式如'task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed'
        - image_type: 图片类型，如'center_inf'或'side_inf'，默认'center_inf'
        - image_id: 图片ID，如'0'、'1'等，默认'0'

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
        'visualization': Optional[str]  # visualize=True时返回图片保存路径，否则None
    }

    注意：当visualize=True时，需要提供task_id、image_type和image_id参数来保存可视化图片。

    Raises:
        PatternDetectionError: 当图案检测失败时
        ImageDimensionError: 当图像尺寸不符合要求时
    """
    try:
        logger.debug("开始图案连续性检测")

        # 验证图像
        if image is None:
            raise PatternDetectionError("图像数据为None")

        if len(image.shape) != 2:
            raise ImageDimensionError("2D", image.shape[:2], "输入图像")

        # 创建配置对象
        config = PatternContinuityConfig.from_dict(conf)
        logger.debug(f"配置加载完成，方法: {kwargs.get('method', 'B')}")

        # 获取额外参数
        method = kwargs.get('method', 'B')
        visualize = kwargs.get('visualize', True)
        task_id = kwargs.get('task_id')
        image_type = kwargs.get('image_type', 'center_inf')
        image_id = kwargs.get('image_id', '0')

        # 提取边缘端点
        try:
            if method.upper() == 'A':
                logger.debug("使用方法A（纯像素操作）检测边缘")
                top_ends, bottom_ends = _detect_with_method_a(image, config)
            elif method.upper() == 'B':
                logger.debug("使用方法B（OpenCV轮廓检测）检测边缘")
                top_ends, bottom_ends = _detect_with_method_b(image, config)
            else:
                raise PatternDetectionError(f"未知检测方法: {method}，请使用'A'或'B'")

            logger.debug(f"边缘端点提取完成: 上边缘{len(top_ends)}个，下边缘{len(bottom_ends)}个")

        except Exception as e:
            raise PatternDetectionError(f"边缘端点提取失败: {str(e)}")

        # 匹配端点
        try:
            matches, unmatched_top, unmatched_bottom = _match_ends(top_ends, bottom_ends, config)
            logger.debug(
                f"端点匹配完成: 匹配{len(matches)}对, "
                f"上边缘未匹配{len(unmatched_top)}个, 下边缘未匹配{len(unmatched_bottom)}个"
            )
        except Exception as e:
            raise ContinuityAnalysisError(f"端点匹配失败: {str(e)}")

        # 判定连续性
        is_continuous = len(unmatched_bottom) == 0
        logger.info(f"连续性判定结果: {'连续' if is_continuous else '不连续'}")

        # 计算评分
        score = config.score if is_continuous else 0
        logger.info(f"评分: {score}")

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
            try:
                vis_image = _visualize_detection(
                    image, top_ends, bottom_ends, matches,
                    unmatched_top, unmatched_bottom, config
                )

                # 保存可视化图片
                if task_id is not None:
                    # 构造保存路径: tests/datasets/task_id_<task_id>/detect_pattern_continuity/<image_type>/<image_id>.png
                    save_dir = Path(f"tests/datasets/{task_id}/detect_pattern_continuity/{image_type}")
                    save_dir.mkdir(parents=True, exist_ok=True)
                    save_path = save_dir / f"{image_id}.png"

                    # 保存图片
                    cv2.imwrite(str(save_path), vis_image)
                    details['visualization'] = str(save_path)
                    logger.debug(f"可视化图片已保存: {save_path}")
                else:
                    # 如果没有提供task_id，返回numpy数组（兼容旧版本）
                    details['visualization'] = vis_image
                    logger.debug("返回numpy数组的可视化结果")
            except Exception as e:
                logger.warning(f"可视化处理失败: {str(e)}，继续返回结果")
                details['visualization'] = None
        else:
            details['visualization'] = None

        return score, details

    except (PatternDetectionError, ImageDimensionError, ContinuityAnalysisError):
        # 重新抛出我们的自定义异常
        raise
    except Exception as e:
        # 捕获其他异常并转换为PatternDetectionError
        logger.error(f"图案连续性检测时发生未知错误: {str(e)}")
        raise PatternDetectionError(f"未知错误: {str(e)}")


def get_adaptive_threshold(image: np.ndarray, config: PatternContinuityConfig) -> int:
    """
    计算自适应阈值

    Parameters:
    - image: 输入灰度图
    - config: 配置对象

    Returns:
    - threshold: 计算得到的阈值

    Raises:
        PatternDetectionError: 当阈值计算失败时
    """
    try:
        if config.adaptive_method == 'otsu':
            # 使用Otsu算法
            threshold, _ = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            logger.debug(f"Otsu阈值: {threshold}")
            return int(threshold)
        elif config.adaptive_method == 'adaptive':
            # 使用中位数或平均值
            threshold = int(np.median(image))
            logger.debug(f"自适应阈值(中位数): {threshold}")
            return threshold
        else:
            raise PatternDetectionError(f"未知的自适应阈值方法: {config.adaptive_method}")

    except Exception as e:
        raise PatternDetectionError(f"自适应阈值计算失败: {str(e)}")


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

    Raises:
        ImageDimensionError: 当图像高度不符合要求时
    """
    try:
        # 验证图像高度
        if image.shape[0] < 2 * config.edge_height:
            raise ImageDimensionError(
                f"Height >= {2 * config.edge_height}",
                image.shape[:2],
                "方法A边缘检测"
            )

        # 计算阈值
        if config.use_adaptive_threshold:
            threshold = get_adaptive_threshold(image, config)
        else:
            threshold = config.threshold
            logger.debug(f"使用固定阈值: {threshold}")

        # 提取上边缘端点
        top_region = image[0:config.edge_height, :]
        top_ends = _extract_ends_from_region(top_region, threshold, config, is_top=True)

        # 提取下边缘端点
        bottom_region = image[-config.edge_height:, :]
        bottom_ends = _extract_ends_from_region(bottom_region, threshold, config, is_top=False)

        return top_ends, bottom_ends

    except ImageDimensionError:
        raise
    except Exception as e:
        raise PatternDetectionError(f"方法A检测失败: {str(e)}")


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

    Raises:
        ImageDimensionError: 当图像高度不符合要求时
        PatternDetectionError: 当轮廓检测失败时
    """
    try:
        # 验证图像高度
        if image.shape[0] < 2 * config.edge_height:
            raise ImageDimensionError(
                f"Height >= {2 * config.edge_height}",
                image.shape[:2],
                "方法B边缘检测"
            )

        # 计算阈值
        if config.use_adaptive_threshold:
            threshold = get_adaptive_threshold(image, config)
        else:
            threshold = config.threshold
            logger.debug(f"使用固定阈值: {threshold}")

        # 二值化
        try:
            _, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY_INV)
        except Exception as e:
            raise PatternDetectionError(f"二值化失败: {str(e)}")

        # 提取上边缘端点
        top_region = binary[0:config.edge_height, :]
        top_ends = _extract_ends_from_contours(top_region, config)

        # 提取下边缘端点
        bottom_region = binary[-config.edge_height:, :]
        bottom_ends = _extract_ends_from_contours(bottom_region, config)

        return top_ends, bottom_ends

    except (ImageDimensionError, PatternDetectionError):
        raise
    except Exception as e:
        raise PatternDetectionError(f"方法B检测失败: {str(e)}")


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
        # 只要有重叠就算连续
        overlap_start = max(top_min_x, bottom_min_x)
        overlap_end = min(top_max_x, bottom_max_x)
        overlap_length = overlap_end - overlap_start + 1

        return overlap_length > 0

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
            rectangle_height = config.vis_rectangle_height
            cv2.rectangle(vis, (min_x, 0), (max_x, rectangle_height), color, config.vis_line_width)

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
            rectangle_bottom_offset = config.vis_rectangle_bottom_offset
            cv2.rectangle(vis, (min_x, h - rectangle_bottom_offset), (max_x, h - 1), color, config.vis_line_width)

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
