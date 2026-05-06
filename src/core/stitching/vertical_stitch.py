# -*- coding: utf-8 -*-
"""
纵图拼接算法模块

提供纯图像处理函数，输入输出都是 PIL.Image 对象。
"""

from PIL import Image
from typing import Tuple


def stitch_and_resize(
    image: Image.Image,
    stitch_count: int,
    target_size: Tuple[int, int]
) -> Image.Image:
    """
    纵向拼接并调整分辨率

    Args:
        image: 输入 PIL.Image 对象
        stitch_count: 拼接次数（将图片纵向复制拼接的次数）
        target_size: 目标尺寸 (width, height)

    Returns:
        Image.Image: 处理后的 PIL.Image 对象

    Raises:
        ValueError: 当参数无效时
    """
    # 参数校验
    if stitch_count < 1:
        raise ValueError(f"stitch_count 必须 >= 1, 当前为 {stitch_count}")

    if not isinstance(target_size, (tuple, list)) or len(target_size) != 2:
        raise ValueError(f"target_size 必须是 (width, height) 格式，当前为 {target_size}")

    # 获取原始图片尺寸
    img_width, img_height = image.size

    # 计算拼接后的尺寸
    stitched_width = img_width
    stitched_height = img_height * stitch_count

    # 创建拼接画布并纵向拼接
    stitched = Image.new("RGB", (stitched_width, stitched_height))
    for i in range(stitch_count):
        stitched.paste(image, (0, i * img_height))

    # 调整尺寸到目标分辨率
    resized = stitched.resize(target_size, Image.LANCZOS)

    return resized
