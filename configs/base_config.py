# -*- coding: utf-8 -*-

"""
基础配置模块

提供系统级配置参数，包括路径设置、默认参数等。
"""

from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path


@dataclass
class SystemConfig:
    """系统配置类，包含路径配置、系统限制和资源配置"""

    # ========== 路径配置 ==========
    # 基础路径，默认为当前工作目录
    base_path: str = "."

    # 输入路径，相对于base_path
    input_path: str = "input"

    # 输出路径，相对于base_path
    output_path: str = "output"

    # 临时文件路径，相对于base_path
    temp_path: str = "temp"

    # 日志文件路径，相对于base_path
    log_path: str = "logs"

    # ========== 系统限制 ==========
    # 最大图片尺寸（像素），超过此尺寸的图片将被缩放
    max_image_size: tuple = (4096, 4096)

    # 最大文件大小（MB），超过此大小的文件将被拒绝
    max_file_size_mb: int = 50

    # 最大批量处理大小
    max_batch_size: int = 100

    # ========== 资源配置 ==========
    # 并发工作线程数
    concurrent_workers: int = 4

    # 是否启用GPU加速
    enable_gpu: bool = False

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'SystemConfig':
        """
        从配置字典创建SystemConfig对象

        Args:
            conf: 配置字典，包含系统配置参数

        Returns:
            SystemConfig: 系统配置对象
        """
        # 处理max_image_size的特殊情况
        config_dict = {}
        for k, v in conf.items():
            if k in cls.__dataclass_fields__:
                if k == 'max_image_size' and isinstance(v, list):
                    config_dict[k] = tuple(v)
                else:
                    config_dict[k] = v

        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        将SystemConfig对象转换为字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'base_path': self.base_path,
            'input_path': self.input_path,
            'output_path': self.output_path,
            'temp_path': self.temp_path,
            'log_path': self.log_path,
            'max_image_size': list(self.max_image_size),  # 转换为列表以便JSON序列化
            'max_file_size_mb': self.max_file_size_mb,
            'max_batch_size': self.max_batch_size,
            'concurrent_workers': self.concurrent_workers,
            'enable_gpu': self.enable_gpu,
        }

    def get_full_input_path(self) -> Path:
        """
        获取完整的输入路径

        Returns:
            Path: 完整的输入路径
        """
        return Path(self.base_path) / self.input_path

    def get_full_output_path(self) -> Path:
        """
        获取完整的输出路径

        Returns:
            Path: 完整的输出路径
        """
        return Path(self.base_path) / self.output_path

    def get_full_temp_path(self) -> Path:
        """
        获取完整的临时文件路径

        Returns:
            Path: 完整的临时文件路径
        """
        return Path(self.base_path) / self.temp_path

    def get_full_log_path(self) -> Path:
        """
        获取完整的日志路径

        Returns:
            Path: 完整的日志路径
        """
        return Path(self.base_path) / self.log_path