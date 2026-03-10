# -*- coding: utf-8 -*-

"""
配置系统入口模块

提供所有配置类的统一导入接口。
"""

from configs.base_config import SystemConfig
from configs.module_config import PreprocessorConfig, InferenceConfig, PostprocessorConfig
from configs.rules_config import (
    PatternContinuityConfig,
    BusinessRules,
    SmallImageFilterRules,
    VerticalStitchRules,
    HorizontalStitchRules,
    ScoringRules
)
from configs.user_config import UserConfig
from configs.complete_config import CompleteConfig

# 配置系统版本
__version__ = "1.0.0"

__all__ = [
    # 基础配置
    'SystemConfig',

    # 模块配置
    'PreprocessorConfig',
    'InferenceConfig',
    'PostprocessorConfig',

    # 规则配置
    'PatternContinuityConfig',
    'BusinessRules',
    'SmallImageFilterRules',
    'VerticalStitchRules',
    'HorizontalStitchRules',
    'ScoringRules',

    # 用户配置
    'UserConfig',

    # 完整配置
    'CompleteConfig',
]