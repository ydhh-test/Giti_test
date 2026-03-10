"""
完整配置文件
整合所有配置模块的入口
"""

from .base_config import (
    PATHS as BASE_PATHS,
    LAND_SEA_RULES,
    DEFAULT_CONF,
    VALID_EXTENSIONS,
)
from .rules_config import (
    LAND_SEA_RATIO_RULES,
    PIXEL_THRESHOLDS,
    SCORING_RULES,
    SCORE_DESCRIPTIONS,
)
from .user_config import USER_SETTINGS
from .postprocessor_config import (
    CONFIG,
    PATHS,
    RIB_CONFIG,
    IMAGE_LIMITS,
    GENERATION_CONFIG,
    INTERNAL_CONFIG,
    SYMMETRY_MAPPING,
    get_path,
    get_rib_count,
    get_generation_mode,
    get_max_per_mode,
)
from .module_config import (
    SERVICES_CONFIG,
    ALGORITHMS_CONFIG,
    UTILS_CONFIG,
)

# 导出所有配置
__all__ = [
    # Base config
    'BASE_PATHS',
    'LAND_SEA_RULES',
    'DEFAULT_CONF',
    'VALID_EXTENSIONS',
    # Rules config
    'LAND_SEA_RATIO_RULES',
    'PIXEL_THRESHOLDS',
    'SCORING_RULES',
    'SCORE_DESCRIPTIONS',
    # User config
    'USER_SETTINGS',
    # Postprocessor config
    'CONFIG',
    'PATHS',
    'RIB_CONFIG',
    'IMAGE_LIMITS',
    'GENERATION_CONFIG',
    'INTERNAL_CONFIG',
    'SYMMETRY_MAPPING',
    'get_path',
    'get_rib_count',
    'get_generation_mode',
    'get_max_per_mode',
    # Module config
    'SERVICES_CONFIG',
    'ALGORITHMS_CONFIG',
    'UTILS_CONFIG',
]
