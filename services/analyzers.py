# -*- coding: utf-8 -*-

"""
几何分析模块

负责几何合理性分析，包括周期检测、海陆比等。
"""

# Copyright © 2026. All rights reserved.
# Author: 桂禹
# AI Assistant: ClaudeCode (Claude Sonnet 4)

from services.analyzers.detect_pattern_continuity import detect_pattern_continuity as detect_pattern_continuity_impl

def detect_pattern_continuity(image, conf, *args, **kwargs):
    """
    检测输入灰度图花纹的连续性

    Args:
        image: 灰度图像 (numpy.ndarray)
        conf: 配置字典，包含评分规则和参数
        *args, **kwargs: 额外参数（method='A'或'B', visualize=True等）

    Returns:
        tuple: (score, details)
            - score (int): 评分（连续返回conf['score']，不连续返回0）
            - details (dict): 详细信息字典

    规则:
        1. 如果上下边缘4像素高度内没有黑色或灰色线条，则连续(返回conf['score'])
        2. 如果有线条，检查所有线条的x轴中心位置是否相差超过4像素
           - 都不超过4像素，则连续(返回conf['score'])
           - 有1组超过4像素，则不连续(返回0)
    """
    return detect_pattern_continuity_impl(image, conf, *args, **kwargs)
