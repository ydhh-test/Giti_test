# -*- coding: utf-8 -*-

"""
计算机视觉工具模块

提供基础图像操作封装，包括缩放、裁剪、颜色转换等。
"""

# Copyright © 2026. All rights reserved.
# Author: 桂禹
# AI Assistant: ClaudeCode (Claude Sonnet 4)

import cv2
import numpy as np
from typing import Union


def add_gray_borders(
    image: Union[str, np.ndarray],
    conf: dict,
    *args,
    **kwargs
) -> np.ndarray:
    """
    在图片左右两侧添加半透明灰色边框

    Args:
        image: 输入图片路径或BGR图像数组
        conf: 配置字典，包含以下键：
            - tire_design_width: 花纹有效宽度（像素）
            - decoration_border_alpha: 灰色叠加透明度（0~1），默认0.5
            - decoration_gray_color: 灰色RGB值，默认(135, 135, 135)
        *args: 预留的位置参数
        **kwargs: 预留的关键字参数

    Returns:
        np.ndarray: 添加灰边后的BGR图像

    Raises:
        ValueError: 当无法读取图片或配置缺失时
    """
    # 1. 从conf中获取配置参数
    content_width = conf.get('tire_design_width')
    if content_width is None:
        raise ValueError("tire_design_width not found in conf")

    alpha = conf.get('decoration_border_alpha', 0.5)
    gray_color = conf.get('decoration_gray_color', (135, 135, 135))

    # 2. 读取图片
    if isinstance(image, str):
        img = cv2.imread(image)
        if img is None:
            raise ValueError(f"无法读取图片: {image}")
    else:
        img = image.copy()

    # 3. 获取原始图片尺寸
    original_height, original_width = img.shape[:2]

    # 4. 计算灰边宽度
    if content_width >= original_width:
        # 无需添加灰边，返回原图
        return img

    if content_width <= 0:
        content_width = 0

    gray_width = (original_width - content_width) // 2

    if gray_width <= 0:
        return img

    # 5. 定义灰色（BGR顺序）
    gray_color_bgr = np.array(gray_color, dtype=np.uint8)

    # 6. 半透明叠加模式
    gray_layer = np.full_like(img, gray_color_bgr, dtype=np.uint8)

    # 7. 分别处理左右区域
    left_region = img[:, :gray_width]
    right_region = img[:, original_width - gray_width:]

    # 8. 混合公式：result = (1-alpha)*原图 + alpha*灰色
    left_blend = cv2.addWeighted(
        left_region, 1-alpha,
        gray_layer[:, :gray_width], alpha,
        0
    )
    right_blend = cv2.addWeighted(
        right_region, 1-alpha,
        gray_layer[:, original_width - gray_width:], alpha,
        0
    )

    # 9. 将混合结果放回原图
    img[:, :gray_width] = left_blend
    img[:, original_width - gray_width:] = right_blend

    return img
