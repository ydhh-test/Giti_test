# -*- coding: utf-8 -*-

"""
后处理配置模块

提供后处理相关的配置参数。
"""

from pathlib import Path

# 项目根目录
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ==========================================
# 横图拼接配置
# ==========================================
HORIZONTAL_STITCH_CONFIG = {
    "rib_count": 5,  # RIB数量: 4或5
    "symmetry_type": "rotate180",  # 对称类型: asymmetric, rotate180, mirror, mirror_shifted, all_symmetry, both, random
    "center_dir": str(_PROJECT_ROOT / "tests" / "datasets" / "horizontal_stitch" / "center"),
    "side_dir": str(_PROJECT_ROOT / "tests" / "datasets" / "horizontal_stitch" / "side-de-gray"),
    "output_dir": str(_PROJECT_ROOT / ".results" / "data" / "horizontal_stitched"),
    "max_per_mode": 10,  # 每种模式最大生成数
    "history_file": ".results/data/history_counts.json",  # 历史计数文件
    "center_size": (200, 1241),  # (宽, 高) - center RIB目标尺寸
    "side_size": (400, 1241),  # (宽, 高) - side RIB目标尺寸
    "blend_width": 10,  # 边缘融合宽度 (像素)
    "main_groove_width": 20,  # 主沟宽度 (像素)
    "image_limits": {
        "side": {"min": 1, "max": 10},
        "center": {"min": 2, "max": 20}
    },
    "symmetry_mapping": {
        "asymmetric": 0,
        "rotate180": 1,
        "mirror": 2,
        "mirror_shifted": 3
    }
}


# ==========================================
# 评分配置
# ==========================================
SCORING_CONFIG = {
    "land_sea_ratio": {
        "target_min": 28.0,  # 目标最小值 (%)
        "target_max": 35.0,  # 目标最大值 (%)
        "margin": 5.0,  # 容差 (%)
        "weight": 1.0  # 权重 (用于总分计算)
    }
}


# ==========================================
# 主配置字典
# ==========================================
CONFIG = {
    "horizontal_stitch_conf": HORIZONTAL_STITCH_CONFIG,
    "calculate_total_score_conf": SCORING_CONFIG
}
