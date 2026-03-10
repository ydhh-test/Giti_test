# -*- coding: utf-8 -*-

"""
IO工具模块

提供文件读写、文件夹遍历等功能。
"""

import cv2
import warnings
from pathlib import Path
from enum import Enum
from .logger import get_logger
from .exceptions import ImageLoadError, ImageSaveError, IOError


class ImageType(Enum):
    """图片类型枚举"""
    PNG = ".png"
    # 预留其他格式
    # JPG = ".jpg"
    # JPEG = ".jpeg"
    # BMP = ".bmp"
    # TIFF = ".tiff"


# 创建模块级日志记录器
logger = get_logger("io_utils")


def load_image(image_path, image_type_enum):
    """
    通用图片加载函数

    Args:
        image_path: 文件路径，支持Path对象或str字符串
        image_type_enum: 图片类型枚举，目前只支持ImageType.PNG

    Returns:
        numpy.ndarray: 加载的灰度图像

    Raises:
        ImageLoadError: 当图片加载失败时
        ValueError: 当image_type_enum不支持时
    """
    try:
        logger.debug(f"开始加载图片: {image_path}")

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
            raise ImageLoadError(str(file_path), "文件不存在")

        # 读取图片为灰度图
        image = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise ImageLoadError(str(file_path), "OpenCV读取失败")

        logger.debug(f"成功加载图片: {file_path}, 尺寸: {image.shape}")
        return image

    except ImageLoadError:
        # 重新抛出我们自定义的异常
        raise
    except Exception as e:
        # 捕获其他异常并转换为ImageLoadError
        logger.error(f"加载图片时发生未知错误: {image_path}, 错误: {str(e)}")
        raise ImageLoadError(str(image_path), f"未知错误: {str(e)}")


def save_image(image, save_path, image_type_enum=ImageType.PNG):
    """
    通用图片保存函数

    Args:
        image: 要保存的图像数据
        save_path: 保存路径，支持Path对象或str字符串
        image_type_enum: 图片类型枚举，默认为PNG

    Raises:
        ImageSaveError: 当图片保存失败时
        ValueError: 当image_type_enum不支持时
    """
    try:
        logger.debug(f"开始保存图片: {save_path}")

        # 检查图片类型是否支持
        if image_type_enum not in ImageType:
            raise ValueError(f"不支持的图片类型: {image_type_enum}. 当前支持的类型: {[t.value for t in ImageType]}")

        # 处理路径
        if isinstance(save_path, str):
            warnings.warn(
                f"建议使用Path对象作为save_path参数，当前传入的是str类型: {save_path}",
                UserWarning,
                stacklevel=2
            )
            file_path = Path(save_path)
        elif isinstance(save_path, Path):
            file_path = save_path
        else:
            raise TypeError(f"save_path参数类型错误，期望Path或str，实际得到: {type(save_path)}")

        # 确保父目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 检查图像数据是否有效
        if image is None:
            raise ImageSaveError(str(file_path), "图像数据为None")

        # 保存图片
        success = cv2.imwrite(str(file_path), image)

        if not success:
            raise ImageSaveError(str(file_path), "OpenCV保存失败")

        logger.debug(f"成功保存图片: {file_path}, 尺寸: {image.shape}")
        return True

    except ImageSaveError:
        # 重新抛出我们自定义的异常
        raise
    except Exception as e:
        # 捕获其他异常并转换为ImageSaveError
        logger.error(f"保存图片时发生未知错误: {save_path}, 错误: {str(e)}")
        raise ImageSaveError(str(save_path), f"未知错误: {str(e)}")
