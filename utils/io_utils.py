# -*- coding: utf-8 -*-

"""
IO工具模块

提供文件读写、文件夹遍历等功能。
"""

# Copyright © 2026 云端辉鸿. All rights reserved.
# Author: 桂禹 <guiyu@cloudhuihong.com>
# AI Assistant: ClaudeCode (Claude Sonnet 4)

import cv2
import warnings
from pathlib import Path
from enum import Enum


class ImageType(Enum):
    """图片类型枚举"""
    PNG = ".png"
    # 预留其他格式
    # JPG = ".jpg"
    # JPEG = ".jpeg"
    # BMP = ".bmp"
    # TIFF = ".tiff"


def load_image(image_path, image_type_enum):
    """
    通用图片加载函数

    Args:
        image_path: 文件路径，支持Path对象或str字符串
        image_type_enum: 图片类型枚举，目前只支持ImageType.PNG

    Returns:
        numpy.ndarray: 加载的灰度图像

    Raises:
        ValueError: 当image_type_enum不支持时
        FileNotFoundError: 当文件不存在时
    """
    # 检查图片类型是否支持
    if image_type_enum not in ImageType:
        raise ValueError(f"不支持的图片类型: {image_type_enum}. 当前支持的类型: {[t.value for t in ImageType]}")

    # 检查路径类型，如果是str给出警告
    if isinstance(image_path, str):
        warnings.warn(
            f"建议使用Path对象作为image_path参数，当前传入的是str类型: {image_path}",
            UserWarning,
            stacklevel=2
        )
        file_path = Path(image_path)
    elif isinstance(image_path, Path):
        file_path = image_path
    else:
        raise TypeError(f"image_path参数类型错误，期望Path或str，实际得到: {type(image_path)}")

    # 检查文件是否存在
    if not file_path.exists():
        raise FileNotFoundError(f"图片文件不存在: {file_path}")

    # 读取图片为灰度图
    image = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise IOError(f"无法读取图片文件: {file_path}")

    return image
