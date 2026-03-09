# -*- coding: utf-8 -*-

"""
完整配置模块

提供完整的配置系统，整合所有配置模块。
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List
from pathlib import Path

from configs.base_config import SystemConfig
from configs.module_config import PreprocessorConfig, InferenceConfig, PostprocessorConfig
from configs.rules_config import BusinessRules, PatternContinuityConfig
from configs.user_config import UserConfig


@dataclass
class CompleteConfig:
    """完整配置类，整合所有配置模块"""

    # 系统配置
    system: SystemConfig = None

    # 预处理配置
    preprocessor: PreprocessorConfig = None

    # 推理配置
    inference: InferenceConfig = None

    # 后处理配置
    postprocessor: PostprocessorConfig = None

    # 业务规则配置
    rules: BusinessRules = None

    # 用户配置
    user: UserConfig = None

    def __post_init__(self):
        """初始化后处理，设置默认值"""
        if self.system is None:
            self.system = SystemConfig()
        if self.preprocessor is None:
            self.preprocessor = PreprocessorConfig()
        if self.inference is None:
            self.inference = InferenceConfig()
        if self.postprocessor is None:
            self.postprocessor = PostprocessorConfig()
        if self.rules is None:
            self.rules = BusinessRules()
        if self.user is None:
            self.user = UserConfig()

    @classmethod
    def from_dict(cls, conf: Dict[str, Any]) -> 'CompleteConfig':
        """
        从配置字典创建CompleteConfig对象

        Args:
            conf: 配置字典，包含完整配置参数

        Returns:
            CompleteConfig: 完整配置对象
        """
        return cls(
            system=SystemConfig.from_dict(conf.get('system', {})),
            preprocessor=PreprocessorConfig.from_dict(conf.get('preprocessor', {})),
            inference=InferenceConfig.from_dict(conf.get('inference', {})),
            postprocessor=PostprocessorConfig.from_dict(conf.get('postprocessor', {})),
            rules=BusinessRules.from_dict(conf.get('rules', {})),
            user=UserConfig.from_dict(conf.get('user', {})),
        )

    @classmethod
    def from_legacy_dict(cls, conf: Dict[str, Any], user_conf: Dict[str, Any] = None) -> 'CompleteConfig':
        """
        从旧格式的配置字典创建CompleteConfig对象（向后兼容）

        Args:
            conf: 旧格式的配置字典
            user_conf: 用户配置字典

        Returns:
            CompleteConfig: 完整配置对象
        """
        if user_conf is None:
            user_conf = {}

        # 合并配置
        merged_conf = {**conf, **user_conf}

        # 构建系统配置
        system_config = {}
        if 'base_path' in merged_conf:
            system_config['base_path'] = merged_conf['base_path']
        if 'input_path' in merged_conf:
            system_config['input_path'] = merged_conf['input_path']
        if 'output_path' in merged_conf:
            system_config['output_path'] = merged_conf['output_path']

        # 构建预处理配置
        preprocessor_config = {}
        if 'target_width' in merged_conf:
            preprocessor_config['target_width'] = merged_conf['target_width']
        if 'target_height' in merged_conf:
            preprocessor_config['target_height'] = merged_conf['target_height']
        if 'convert_to_grayscale' in merged_conf:
            preprocessor_config['convert_to_grayscale'] = merged_conf['convert_to_grayscale']

        # 构建推理配置
        inference_config = {}
        if 'model_name' in merged_conf:
            inference_config['model_name'] = merged_conf['model_name']
        if 'device' in merged_conf:
            inference_config['device'] = merged_conf['device']

        # 构建后处理配置
        postprocessor_config = {}
        if 'output_format' in merged_conf:
            postprocessor_config['output_format'] = merged_conf['output_format']
        if 'quality' in merged_conf:
            postprocessor_config['quality'] = merged_conf['quality']

        # 构建业务规则配置
        rules_config = {}
        if 'pattern_continuity_conf' in merged_conf:
            rules_config['pattern_continuity'] = merged_conf['pattern_continuity_conf']
        if 'small_image_filter_conf' in merged_conf:
            rules_config['small_image_filter'] = merged_conf['small_image_filter_conf']
        if 'vertical_stitch_conf' in merged_conf:
            rules_config['vertical_stitch'] = merged_conf['vertical_stitch_conf']
        if 'horizontal_stitch_conf' in merged_conf:
            rules_config['horizontal_stitch'] = merged_conf['horizontal_stitch_conf']

        # 构建用户配置
        user_config = {}
        if 'enable_visualization' in merged_conf:
            user_config['enable_visualization'] = merged_conf['enable_visualization']
        if 'debug_mode' in merged_conf:
            user_config['debug_mode'] = merged_conf['debug_mode']
        if 'verbose_logging' in merged_conf:
            user_config['verbose_logging'] = merged_conf['verbose_logging']
        if 'save_debug_images' in merged_conf:
            user_config['save_debug_images'] = merged_conf['save_debug_images']
        if 'include_metadata' in merged_conf:
            user_config['include_metadata'] = merged_conf['include_metadata']

        return cls(
            system=SystemConfig(**system_config),
            preprocessor=PreprocessorConfig(**preprocessor_config),
            inference=InferenceConfig(**inference_config),
            postprocessor=PostprocessorConfig(**postprocessor_config),
            rules=BusinessRules.from_dict(rules_config),
            user=UserConfig(**user_config),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        将CompleteConfig对象转换为字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'system': self.system.to_dict(),
            'preprocessor': self.preprocessor.to_dict(),
            'inference': self.inference.to_dict(),
            'postprocessor': self.postprocessor.to_dict(),
            'rules': self.rules.to_dict(),
            'user': self.user.to_dict(),
        }

    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        转换为旧格式的配置字典（向后兼容）

        Returns:
            Dict[str, Any]: 旧格式的配置字典
        """
        conf = {
            'system': self.system.to_dict(),
            'preprocessor': self.preprocessor.to_dict(),
            'inference': self.inference.to_dict(),
            'postprocessor': self.postprocessor.to_dict(),
            'rules': self.rules.to_dict(),
            'user': self.user.to_dict(),
        }

        # 展开嵌套配置以兼容旧格式
        merged_conf = {}
        for section in conf.values():
            merged_conf.update(section)

        # 特别处理rules部分
        if 'pattern_continuity' in merged_conf:
            merged_conf['pattern_continuity_conf'] = merged_conf['pattern_continuity']
            del merged_conf['pattern_continuity']
        if 'small_image_filter' in merged_conf:
            merged_conf['small_image_filter_conf'] = merged_conf['small_image_filter']
            del merged_conf['small_image_filter']
        if 'vertical_stitch' in merged_conf:
            merged_conf['vertical_stitch_conf'] = merged_conf['vertical_stitch']
            del merged_conf['vertical_stitch']
        if 'horizontal_stitch' in merged_conf:
            merged_conf['horizontal_stitch_conf'] = merged_conf['horizontal_stitch']
            del merged_conf['horizontal_stitch']

        return merged_conf

    def validate(self) -> tuple[bool, List[str]]:
        """
        验证配置的有效性

        Returns:
            tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        # 验证系统配置
        if self.system.max_file_size_mb <= 0:
            errors.append("system.max_file_size_mb must be positive")

        if self.system.max_batch_size <= 0:
            errors.append("system.max_batch_size must be positive")

        if self.system.concurrent_workers <= 0:
            errors.append("system.concurrent_workers must be positive")

        # 验证预处理配置
        if self.preprocessor.target_width <= 0 or self.preprocessor.target_height <= 0:
            errors.append("preprocessor.target_width and target_height must be positive")

        if self.preprocessor.normalization not in ['minmax', 'standard']:
            errors.append("preprocessor.normalization must be 'minmax' or 'standard'")

        # 验证推理配置
        if self.inference.batch_size <= 0:
            errors.append("inference.batch_size must be positive")

        if self.inference.device not in ['cpu', 'cuda']:
            errors.append("inference.device must be 'cpu' or 'cuda'")

        if self.inference.precision not in ['float32', 'float16']:
            errors.append("inference.precision must be 'float32' or 'float16'")

        if not (0 <= self.inference.confidence_threshold <= 1):
            errors.append("inference.confidence_threshold must be between 0 and 1")

        # 验证后处理配置
        valid_formats = ['png', 'jpeg', 'webp']
        if self.postprocessor.output_format not in valid_formats:
            errors.append(f"postprocessor.output_format must be one of {valid_formats}")

        if not (1 <= self.postprocessor.quality <= 100):
            errors.append("postprocessor.quality must be between 1 and 100")

        if self.postprocessor.default_stitch_direction not in ['vertical', 'horizontal']:
            errors.append("postprocessor.default_stitch_direction must be 'vertical' or 'horizontal'")

        # 验证用户配置
        if self.user.visualization_quality < 1 or self.user.visualization_quality > 100:
            errors.append("user.visualization_quality must be between 1 and 100")

        if self.user.debug_log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            errors.append("user.debug_log_level must be 'DEBUG', 'INFO', 'WARNING', or 'ERROR'")

        return len(errors) == 0, errors

    def get_input_directory(self) -> Path:
        """
        获取输入目录路径

        Returns:
            Path: 输入目录路径
        """
        return self.system.get_full_input_path()

    def get_output_directory(self) -> Path:
        """
        获取输出目录路径

        Returns:
            Path: 输出目录路径
        """
        return self.user.get_output_directory(self.system.get_full_output_path())

    def get_temp_directory(self) -> Path:
        """
        获取临时目录路径

        Returns:
            Path: 临时目录路径
        """
        return self.system.get_full_temp_path()

    def get_log_directory(self) -> Path:
        """
        获取日志目录路径

        Returns:
            Path: 日志目录路径
        """
        return self.system.get_full_log_path()

    def get_debug_images_directory(self) -> Path:
        """
        获取调试图片目录路径

        Returns:
            Path: 调试图片目录路径
        """
        return self.user.get_debug_images_directory(self.system.get_full_output_path())

    def is_debug_mode(self) -> bool:
        """
        判断是否处于调试模式

        Returns:
            bool: 是否处于调试模式
        """
        return self.user.debug_mode or self.user.verbose_logging

    def should_save_visualization(self) -> bool:
        """
        判断是否应该保存可视化结果

        Returns:
            bool: 是否应该保存可视化结果
        """
        return self.user.enable_visualization

    def should_save_debug_images(self) -> bool:
        """
        判断是否应该保存调试图片

        Returns:
            bool: 是否应该保存调试图片
        """
        return self.user.save_debug_images or self.is_debug_mode()