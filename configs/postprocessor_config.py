# -*- coding: utf-8 -*-

"""
后处理配置模块

提供后处理相关的配置参数，支持 9 阶段处理流程。

部署说明：
- 所有路径均位于 .results 目录下（项目根目录的子目录）
- 使用 Path 确保路径分隔符跨平台兼容（Windows: \, Linux/macOS: /）
- 测试数据由测试准备函数从 tests/datasets 拷贝到 .results
"""

from pathlib import Path

# 项目根目录
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 结果目录（位于项目根目录下）
_RESULTS_DIR = _PROJECT_ROOT / ".results"


# ==========================================
# 小图筛选配置
# ==========================================
SMALL_IMAGE_FILTER_CONFIG = {
    "min_width": 100,  # 最小宽度 (像素)
    "min_height": 100,  # 最小高度 (像素)
    "min_area": 10000,  # 最小面积 (像素²)
    "input_dir": str(_RESULTS_DIR / "data" / "small_images"),  # 输入目录
}


# ==========================================
# 小图打分配置
# ==========================================
SMALL_IMAGE_SCORE_CONFIG = {
    "score_method": "rule_based",  # 打分方法：rule_based, ml_based
    "output_score_file": str(_RESULTS_DIR / "data" / "small_image_scores.json"),
}


# ==========================================
# 纵图拼接配置
# ==========================================
VERTICAL_STITCH_CONFIG = {
    "rib_count": 4,  # RIB 数量
    "input_dir": str(_RESULTS_DIR / "data" / "vertical_stitch"),  # 输入目录
    "output_dir": str(_RESULTS_DIR / "data" / "vertical_stitched"),
    "blend_width": 10,  # 边缘融合宽度 (像素)
}


# ==========================================
# 横图拼接配置
# ==========================================
HORIZONTAL_STITCH_CONFIG = {
    "rib_count": 5,  # RIB 数量：4 或 5
    "symmetry_type": "rotate180",  # 对称类型：asymmetric, rotate180, mirror, mirror_shifted, all_symmetry, both, random
    "center_dir": str(_RESULTS_DIR / "data" / "horizontal_stitch" / "center"),  # center RIB 输入目录
    "side_dir": str(_RESULTS_DIR / "data" / "horizontal_stitch" / "side-de-gray"),  # side RIB 输入目录
    "output_dir": str(_RESULTS_DIR / "data" / "horizontal_stitched"),
    "max_per_mode": 10,  # 每种模式最大生成数
    "history_file": str(_RESULTS_DIR / "data" / "history_counts.json"),  # 历史计数文件
    "center_size": (200, 1241),  # (宽，高) - center RIB 目标尺寸
    "side_size": (400, 1241),  # (宽，高) - side RIB 目标尺寸
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
# 横图打分配置
# ==========================================
HORIZONTAL_IMAGE_SCORE_CONFIG = {
    "score_method": "land_sea_ratio",  # 打分方法
    "land_sea_ratio": {
        "target_min": 28.0,  # 目标最小值 (%)
        "target_max": 35.0,  # 目标最大值 (%)
        "margin": 5.0,  # 容差 (%)
    }
}


# ==========================================
# 装饰边框配置
# ==========================================
DECORATION_CONFIG = {
    "decoration_style": "simple",  # 装饰风格：simple
    "decoration_border_alpha": 0.5,  # 装饰边框透明度
    "tire_design_width": 200,  # 轮胎花纹宽度
}


# ==========================================
# 统计总分配置
# ==========================================
CALCULATE_TOTAL_SCORE_CONFIG = {
    "land_sea_ratio": {
        "target_min": 28.0,  # 目标最小值 (%)
        "target_max": 35.0,  # 目标最大值 (%)
        "margin": 5.0,  # 容差 (%)
        "weight": 1.0  # 权重 (用于总分计算)
    }
}


# ==========================================
# 整理输出配置
# ==========================================
STANDARD_INPUT_CONFIG = {
    "sort_by": "score_desc",  # 排序方式：score_desc(高分优先), name_asc(名字母序)
    "output_dir": str(_RESULTS_DIR / "output"),
    "include_score_details": True,  # 是否包含打分详情
}


# ==========================================
# 主配置字典
# ==========================================
CONFIG = {
    "small_image_filter_conf": SMALL_IMAGE_FILTER_CONFIG,
    "small_image_score_conf": SMALL_IMAGE_SCORE_CONFIG,
    "vertical_stitch_conf": VERTICAL_STITCH_CONFIG,
    "horizontal_stitch_conf": HORIZONTAL_STITCH_CONFIG,
    "horizontal_image_score_conf": HORIZONTAL_IMAGE_SCORE_CONFIG,
    "decoration_conf": DECORATION_CONFIG,
    "calculate_total_score_conf": CALCULATE_TOTAL_SCORE_CONFIG,
    "standard_input_conf": STANDARD_INPUT_CONFIG,
}
