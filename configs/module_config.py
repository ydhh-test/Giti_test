# -*- coding: utf-8 -*-

"""
模块配置模块

提供预处理、推理、后处理等模块的配置参数。
"""

# Copyright © 2026 云端辉鸿. All rights reserved.
# Author: 桂禹 <guiyu@cloudhuihong.com>
# AI Assistant: ClaudeCode (Claude Sonnet 4)

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class PreprocessorConfig:
    """预处理配置类，包含图像预处理相关参数"""

    # ========== 图像处理参数 ==========
    # 目标图像宽度（像素）
    target_width: int = 1024

    # 目标图像高度（像素）
    target_height: int = 1024

    # 是否保持宽高比
    keep_aspect_ratio: bool = True

    # 图像归一化方法：'minmax'或'standard'
    normalization: str = 'minmax'

    # 是否启用高斯模糊
    enable_gaussian_blur: bool = False

    # 高斯模糊核大小
    gaussian_kernel_size: int = 5

    # 是否启用图像增强
    enable_augmentation: bool = False

    # ========== 灰度转换参数 ==========
    # 是否转换为灰度图
    convert_to_grayscale: bool = True

    # 灰度转换方法：'cv2'或'weighted'
    grayscale_method: str = 'cv2'

    # RGB转灰度的权重（当grayscale_method='weighted'时使用）
    rgb_weights: tuple = (0.299, 0.587, 0.114)

    # ========== 边缘检测参数 ==========
    # 是否启用边缘检测
    enable_edge_detection: bool = True

    # 边缘检测方法：'canny'或'sobel'
    edge_detection_method: str = 'canny'

    # Canny边缘检测低阈值
    canny_threshold1: int = 50

    # Canny边缘检测高阈值
    canny_threshold2: int = 150

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'PreprocessorConfig':
        """
        从配置字典创建PreprocessorConfig对象

        Args:
            conf: 配置字典，包含预处理配置参数

        Returns:
            PreprocessorConfig: 预处理配置对象
        """
        # 处理rgb_weights的特殊情况
        config_dict = {}
        for k, v in conf.items():
            if k in cls.__dataclass_fields__:
                if k == 'rgb_weights' and isinstance(v, list):
                    config_dict[k] = tuple(v)
                else:
                    config_dict[k] = v

        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        将PreprocessorConfig对象转换为字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'target_width': self.target_width,
            'target_height': self.target_height,
            'keep_aspect_ratio': self.keep_aspect_ratio,
            'normalization': self.normalization,
            'enable_gaussian_blur': self.enable_gaussian_blur,
            'gaussian_kernel_size': self.gaussian_kernel_size,
            'enable_augmentation': self.enable_augmentation,
            'convert_to_grayscale': self.convert_to_grayscale,
            'grayscale_method': self.grayscale_method,
            'rgb_weights': list(self.rgb_weights),
            'enable_edge_detection': self.enable_edge_detection,
            'edge_detection_method': self.edge_detection_method,
            'canny_threshold1': self.canny_threshold1,
            'canny_threshold2': self.canny_threshold2,
        }


@dataclass
class InferenceConfig:
    """推理配置类，包含模型推理相关参数"""

    # ========== 模型参数 ==========
    # 模型名称或路径
    model_name: str = "default_model"

    # 模型版本
    model_version: str = "1.0"

    # 推理设备：'cpu'或'cuda'
    device: str = "cpu"

    # 批处理大小
    batch_size: int = 1

    # 推理精度：'float32'或'float16'
    precision: str = "float32"

    # ========== 后处理参数 ==========
    # 置信度阈值
    confidence_threshold: float = 0.5

    # NMS IOU阈值
    nms_threshold: float = 0.45

    # 最大检测数量
    max_detections: int = 100

    # ========== 性能参数 ==========
    # 是否启用模型优化
    enable_optimization: bool = False

    # 是否启用混合精度
    enable_mixed_precision: bool = False

    # 是否启用模型缓存
    enable_cache: bool = True

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'InferenceConfig':
        """
        从配置字典创建InferenceConfig对象

        Args:
            conf: 配置字典，包含推理配置参数

        Returns:
            InferenceConfig: 推理配置对象
        """
        return cls(**{k: v for k, v in conf.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """
        将InferenceConfig对象转换为字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'model_name': self.model_name,
            'model_version': self.model_version,
            'device': self.device,
            'batch_size': self.batch_size,
            'precision': self.precision,
            'confidence_threshold': self.confidence_threshold,
            'nms_threshold': self.nms_threshold,
            'max_detections': self.max_detections,
            'enable_optimization': self.enable_optimization,
            'enable_mixed_precision': self.enable_mixed_precision,
            'enable_cache': self.enable_cache,
        }


@dataclass
class PostprocessorConfig:
    """后处理配置类，包含图像后处理相关参数"""

    # ========== 图像输出参数 ==========
    # 输出图像格式：'png', 'jpeg', 'webp'等
    output_format: str = "png"

    # JPEG/WebP质量（1-100）
    quality: int = 95

    # 支持的图像扩展名（用于文件查找）
    supported_image_extensions: List[str] = None

    # ========== 拼接参数 ==========
    # 默认拼接方向：'vertical'或'horizontal'
    default_stitch_direction: str = "vertical"

    # 拼接重叠区域像素数
    stitch_overlap_pixels: int = 0

    # 是否启用图像裁剪
    enable_crop: bool = False

    # 裁剪边距（像素）
    crop_margin: int = 10

    # ========== 图像质量参数 ==========
    # 是否启用图像去噪
    enable_denoising: bool = False

    # 去噪强度（1-10）
    denoising_strength: int = 5

    # 是否启用图像锐化
    enable_sharpening: bool = False

    # 锐化强度（1-10）
    sharpening_strength: int = 3

    def __post_init__(self):
        """初始化后处理，设置默认值"""
        if self.supported_image_extensions is None:
            self.supported_image_extensions = ['.png']

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'PostprocessorConfig':
        """
        从配置字典创建PostprocessorConfig对象

        Args:
            conf: 配置字典，包含后处理配置参数

        Returns:
            PostprocessorConfig: 后处理配置对象
        """
        config_dict = {k: v for k, v in conf.items() if k in cls.__dataclass_fields__}
        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        将PostprocessorConfig对象转换为字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'output_format': self.output_format,
            'quality': self.quality,
            'supported_image_extensions': self.supported_image_extensions,
            'default_stitch_direction': self.default_stitch_direction,
            'stitch_overlap_pixels': self.stitch_overlap_pixels,
            'enable_crop': self.enable_crop,
            'crop_margin': self.crop_margin,
            'enable_denoising': self.enable_denoising,
            'denoising_strength': self.denoising_strength,
            'enable_sharpening': self.enable_sharpening,
            'sharpening_strength': self.sharpening_strength,
        }