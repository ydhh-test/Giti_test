"""
图像处理工具模块
提供常用的OpenCV图像处理辅助函数
"""

import cv2
import numpy as np
from typing import Tuple, Optional


def read_image_chinese_path(img_path: str) -> Optional[np.ndarray]:
    """
    使用cv2.imdecode读取图像，支持中文路径

    Args:
        img_path: 图像文件路径

    Returns:
        读取的图像数组，读取失败返回None
    """
    return cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)


def save_image_chinese_path(img_path: str, img: np.ndarray) -> bool:
    """
    使用cv2.imencode保存图像，支持中文路径

    Args:
        img_path: 图像文件路径
        img: 要保存的图像数组

    Returns:
        保存成功返回True，否则返回False
    """
    is_success, buffer = cv2.imencode(".png", img)
    if is_success:
        buffer.tofile(img_path)
        return True
    return False


def rgb_to_gray(img: np.ndarray) -> np.ndarray:
    """
    将RGB/BGR图像转换为灰度图

    Args:
        img: 输入图像（BGR格式）

    Returns:
        灰度图
    """
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def apply_threshold(img: np.ndarray, lower: int, upper: int) -> np.ndarray:
    """
    应用灰度阈值范围生成掩码

    Args:
        img: 灰度图像
        lower: 下界
        upper: 上界

    Returns:
        二值化掩码
    """
    return cv2.inRange(img, lower, upper)


def count_nonzero_pixels(mask: np.ndarray) -> int:
    """
    统计掩码中非零像素数量

    Args:
        mask: 二值化掩码

    Returns:
        非零像素数量
    """
    return cv2.countNonZero(mask)


def resize_image(img: np.ndarray, width: int, height: int,
                 interpolation: int = cv2.INTER_LINEAR) -> np.ndarray:
    """
    调整图像大小

    Args:
        img: 输入图像
        width: 目标宽度
        height: 目标高度
        interpolation: 插值方法

    Returns:
        调整后的图像
    """
    return cv2.resize(img, (width, height), interpolation=interpolation)


def crop_center(img: np.ndarray, crop_width: int, crop_height: int) -> np.ndarray:
    """
    从图像中心裁剪指定大小

    Args:
        img: 输入图像
        crop_width: 裁剪宽度
        crop_height: 裁剪高度

    Returns:
        裁剪后的图像
    """
    h, w = img.shape[:2]
    start_x = (w - crop_width) // 2
    start_y = (h - crop_height) // 2
    return img[start_y:start_y + crop_height, start_x:start_x + crop_width]


def create_blend_mask(width: int, blend_width: int,
                      is_first: bool = False, is_last: bool = False) -> np.ndarray:
    """
    创建边缘融合掩码

    Args:
        width: 图像宽度
        blend_width: 融合宽度
        is_first: 是否是第一个（左侧不融合）
        is_last: 是否是最后一个（右侧不融合）

    Returns:
        融合掩码
    """
    mask = np.ones((1, width, 1), dtype=np.float32)

    if not is_first:
        mask[:, :blend_width, :] = np.linspace(0.0, 1.0, blend_width).reshape(1, blend_width, 1)
    if not is_last:
        mask[:, -blend_width:, :] = np.linspace(1.0, 0.0, blend_width).reshape(1, blend_width, 1)

    return mask


def apply_blend(img: np.ndarray, blend_width: int,
                is_first: bool = False, is_last: bool = False) -> np.ndarray:
    """
    应用边缘融合

    Args:
        img: 输入图像
        blend_width: 融合宽度
        is_first: 是否是第一个
        is_last: 是否是最后一个

    Returns:
        融合后的图像
    """
    h, w, c = img.shape

    if w <= 2 * blend_width:
        return img

    mask = create_blend_mask(w, blend_width, is_first, is_last)
    return (img.astype(np.float32) * mask).astype(np.uint8)
