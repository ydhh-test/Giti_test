# -*- coding: utf-8 -*-

"""
用户配置模块

提供用户自定义的配置参数，包括可视化、调试、输出等选项。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path


# ========== 模块级常量：默认配置 ==========

# 纵图拼接默认配置
DEFAULT_VERTICAL_STITCH_CONF = {
    "center_vertical": {"resolution": [200, 1241]},
    "side_vertical": {"resolution": [400, 1241]},
    "center_count": 5,
    "side_count": 5,
}

# 横图拼接默认配置
DEFAULT_HORIZONTAL_STITCH_CONF = {
    "rib_count": 5,  # RIB 数量 (4 或 5)
    "symmetry_type": "both",  # 对称类型：asymmetric/rotate180/mirror/mirror_shifted/random/all_symmetry/both
    "blend_width": 10,  # 边缘融合宽度 (像素)
    "main_groove_width": 20,  # 主沟宽度 (像素)
    "generation": {
        "max_per_mode": 10,  # 每种模式最大生成数
    },
    "symmetry_mapping": {  # 对称模式文件名映射
        "asymmetric": 0,
        "rotate180": 1,
        "mirror": 2,
        "mirror_shifted": 3,
    },
    "history_file": None,  # 由调用方动态设置，默认为 None 表示不启用历史计数
}

# RIB 横向连续性拼接默认配置（rule12/16/17）
DEFAULT_RIB_CONTINUITY_CONF = {
    "input_dir": "combine_horizontal",
    "output_dir": "rib_continuity",
    "continuity_mode": "none",
    "groove_width_mm": 10.0,
    "pixel_per_mm": 2.0,
    "blend_width": 10,
    "edge_continuity": {},
}

# 横图打分默认配置
DEFAULT_HORIZONTAL_IMAGE_SCORE_CONF = {
    "input_dir": "combine_horizontal",
    "visualize": True,
    "output_base_dir": ".results",
    "land_sea_ratio": {
        "target_min": 28.0,
        "target_max": 35.0,
        "margin": 5.0
    }
}


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

    # ========== 轮胎尺寸参数 ==========
    # 花纹有效宽度（像素）
    tire_design_width: int = 1000

    # 轮胎总宽度（像素）
    tire_total_width: int = 1200

    # ========== 纵图拼接参数 ==========
    # 纵图拼接配置（默认值来自 DEFAULT_VERTICAL_STITCH_CONF）
    vertical_stitch_conf: Dict[str, Any] = field(default_factory=dict)

    # ========== RIB 横向连续性拼接参数（rule12/16/17）==========
    # 是否启用 RIB 连续性拼接（替代 rule1to5 横图拼接）
    enable_rib_continuity: bool = False

    # RIB 连续性拼接配置（默认值来自 DEFAULT_RIB_CONTINUITY_CONF）
    rib_continuity_conf: Dict[str, Any] = field(default_factory=dict)

    # ========== 装饰边框参数 ==========
    # 灰色透明度（0~1）
    decoration_border_alpha: float = 0.5

    # 装饰风格：'simple', 'gradient', 'pattern'等
    decoration_style: str = 'simple'

    # 灰色RGB值
    decoration_gray_color: tuple[int, int, int] = (135, 135, 135)

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
            'tire_design_width': self.tire_design_width,
            'tire_total_width': self.tire_total_width,
            'decoration_border_alpha': self.decoration_border_alpha,
            'decoration_style': self.decoration_style,
            'decoration_gray_color': self.decoration_gray_color,
            'vertical_stitch_conf': self.vertical_stitch_conf,
            'enable_rib_continuity': self.enable_rib_continuity,
            'rib_continuity_conf': self.rib_continuity_conf,
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