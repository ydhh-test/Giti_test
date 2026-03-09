# -*- coding: utf-8 -*-

"""
用户配置模块

提供用户自定义的配置参数，包括可视化、调试、输出等选项。
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class UserConfig:
    """用户配置类，包含用户自定义的可视化、调试、输出等选项"""

    # ========== 可视化选项 ==========
    # 是否启用可视化
    enable_visualization: bool = True

    # 是否保存中间结果
    save_intermediate_results: bool = False

    # 可视化输出格式：'png', 'jpeg', 'webp'等
    visualization_format: str = "png"

    # 可视化质量（1-100）
    visualization_quality: int = 95

    # 是否显示处理进度
    show_progress: bool = True

    # ========== 调试选项 ==========
    # 是否启用详细日志记录
    verbose_logging: bool = False

    # 是否启用调试模式
    debug_mode: bool = False

    # 调试日志级别：'DEBUG', 'INFO', 'WARNING', 'ERROR'
    debug_log_level: str = "DEBUG"

    # 是否打印调试信息到控制台
    print_debug_info: bool = True

    # 是否保存调试信息到文件
    save_debug_info_to_file: bool = False

    # ========== 输出选项 ==========
    # 自定义输出目录（如果为None则使用默认输出目录）
    custom_output_dir: Optional[str] = None

    # 是否保存调试图片
    save_debug_images: bool = False

    # 调试图片保存路径（相对于输出目录）
    debug_images_path: str = "debug_images"

    # 是否在输出中包含元数据
    include_metadata: bool = True

    # 是否保存处理时间统计
    save_timing_stats: bool = False

    # ========== 其他选项 ==========
    # 是否启用性能分析
    enable_profiling: bool = False

    # 是否保存配置快照
    save_config_snapshot: bool = True

    # 处理超时时间（秒），0表示无超时
    timeout_seconds: int = 0

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'UserConfig':
        """
        从配置字典创建UserConfig对象

        Args:
            conf: 配置字典，包含用户配置参数

        Returns:
            UserConfig: 用户配置对象
        """
        return cls(**{k: v for k, v in conf.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """
        将UserConfig对象转换为字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'enable_visualization': self.enable_visualization,
            'save_intermediate_results': self.save_intermediate_results,
            'visualization_format': self.visualization_format,
            'visualization_quality': self.visualization_quality,
            'show_progress': self.show_progress,
            'verbose_logging': self.verbose_logging,
            'debug_mode': self.debug_mode,
            'debug_log_level': self.debug_log_level,
            'print_debug_info': self.print_debug_info,
            'save_debug_info_to_file': self.save_debug_info_to_file,
            'custom_output_dir': self.custom_output_dir,
            'save_debug_images': self.save_debug_images,
            'debug_images_path': self.debug_images_path,
            'include_metadata': self.include_metadata,
            'save_timing_stats': self.save_timing_stats,
            'enable_profiling': self.enable_profiling,
            'save_config_snapshot': self.save_config_snapshot,
            'timeout_seconds': self.timeout_seconds,
        }

    def get_output_directory(self, base_output_dir: Path) -> Path:
        """
        获取输出目录路径

        Args:
            base_output_dir: 基础输出目录

        Returns:
            Path: 输出目录路径
        """
        if self.custom_output_dir:
            return Path(self.custom_output_dir)
        return base_output_dir

    def get_debug_images_directory(self, base_output_dir: Path) -> Path:
        """
        获取调试图片保存目录

        Args:
            base_output_dir: 基础输出目录

        Returns:
            Path: 调试图片目录路径
        """
        output_dir = self.get_output_directory(base_output_dir)
        return output_dir / self.debug_images_path

    def should_save_debug(self) -> bool:
        """
        判断是否应该保存调试信息

        Returns:
            bool: 是否应该保存调试信息
        """
        return self.save_debug_images or self.save_debug_info_to_file or self.save_timing_stats