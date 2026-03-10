"""
后处理配置文件
包含RIB拼接、对称模式等配置
"""

from pathlib import Path

# 项目根目录（configs 的上一级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 直接使用 Python 字典定义配置（路径相对项目根，便于任意目录克隆后使用）
# 测试数据目录: tests/datasets/split/center 和 tests/datasets/split/side-de-gray
# 运行输出目录: .results/data/whole_img
CONFIG = {
    "paths": {
        "center_dir": str(_PROJECT_ROOT / "tests" / "datasets" / "split" / "center"),
        "side_dir": str(_PROJECT_ROOT / "tests" / "datasets" / "split" / "side-de-gray"),
        "output_dir": str(_PROJECT_ROOT / ".results" / "data" / "whole_img")
    },
    "rib": {"count": 5},
    "image_limits": {},
    "generation": {"mode": "rotate180", "max_per_mode": 10},
    "internal": {"blend_width": 10, "main_groove_width": 30},
    "symmetry_mapping": {
        "asymmetric": 0,
        "rotate180": 1,
        "mirror": 2,
        "mirror_shifted": 3
    }
}


# 路径配置
PATHS = CONFIG.get('paths', {})

# RIB配置
RIB_CONFIG = CONFIG.get('rib', {})

# 图片数量限制
IMAGE_LIMITS = CONFIG.get('image_limits', {})

# 生成配置
GENERATION_CONFIG = CONFIG.get('generation', {})

# 内部参数
INTERNAL_CONFIG = CONFIG.get('internal', {})

# 对称模式映射
SYMMETRY_MAPPING = CONFIG.get('symmetry_mapping', {})


# 辅助函数
def get_path(key: str) -> str:
    """获取路径配置"""
    return PATHS.get(key, "")


def get_rib_count() -> int:
    """获取RIB数量"""
    return RIB_CONFIG.get('count', 5)


def get_generation_mode() -> str:
    """获取生成模式"""
    return GENERATION_CONFIG.get('mode', 'both')


def get_max_per_mode() -> int:
    """获取每种模式生成的上限"""
    return GENERATION_CONFIG.get('max_per_mode', 10)
