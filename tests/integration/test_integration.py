#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""简单的集成测试脚本"""

import numpy as np
import sys

print("=" * 60)
print("集成测试 - land_sea_ratio 和 HorizontalStitch")
print("=" * 60)
print()

# 测试1: land_sea_ratio
print("【测试1】验证 land_sea_ratio 功能")
print("-" * 60)

from rules.scoring.land_sea_ratio import compute_land_sea_ratio, compute_black_area, compute_gray_area

# 测试黑色区域
img1 = np.zeros((100, 100, 3), dtype=np.uint8)
img1[:50, :] = 30
img1[50:, :] = 255
black_area = compute_black_area(img1)
print(f"  黑色区域计算: {black_area} (预期: 5000)")
assert black_area == 5000

# 测试灰色区域
img2 = np.zeros((100, 100, 3), dtype=np.uint8)
img2[:50, :] = 100
img2[50:, :] = 255
gray_area = compute_gray_area(img2)
print(f"  灰色区域计算: {gray_area} (预期: 5000)")
assert gray_area == 5000

# 测试海陆比评分
img3 = np.zeros((100, 100, 3), dtype=np.uint8)
img3[:30, :] = 30
img3[30:, :] = 255
conf = {"target_min": 28.0, "target_max": 35.0, "margin": 5.0}
score, details = compute_land_sea_ratio(img3, conf)
print(f"  海陆比评分: score={score}, ratio={details['ratio_value']}%")
assert score == 2

print("  ✓ land_sea_ratio 测试通过!")
print()

# 测试2: HorizontalStitch初始化
print("【测试2】验证 HorizontalStitch 类")
print("-" * 60)

from algorithms.stitching.horizontal_stitch import HorizontalStitch, CombinationManager, LayoutResult

# 测试LayoutResult
img = np.zeros((100, 200, 3), dtype=np.uint8)
result = LayoutResult(
    layout_image=img,
    applied_symmetry="mirror",
    shift_offset=0.0,
    rib_regions=[(0, 0, 100, 100)],
    layout_score=8.0,
    rib_combination=(0, 1, 2, 3, 4)
)
print(f"  LayoutResult创建成功: symmetry={result.applied_symmetry}, score={result.layout_score}")
assert result.applied_symmetry == "mirror"

# 测试CombinationManager
center_images = [np.zeros((100, 100, 3)) for _ in range(3)]
side_images = [np.zeros((100, 100, 3)) for _ in range(2)]
config = {"max_per_mode": 5, "history_file": ".results/data/test_history.json"}
manager = CombinationManager(center_images, side_images, 5, config)
print(f"  CombinationManager创建成功: {len(manager.asymmetric_combinations)} 个组合")
assert len(manager.asymmetric_combinations) > 0

# 测试HorizontalStitch初始化
conf = {
    "rib_count": 5,
    "symmetry_type": "asymmetric",
    "center_dir": "tests/datasets/horizontal_stitch/center",
    "side_dir": "tests/datasets/horizontal_stitch/side-de-gray",
    "output_dir": ".results/test_output"
}
stitcher = HorizontalStitch("test_task", conf)
print(f"  HorizontalStitch创建成功: task_id={stitcher.task_id}, rib_count={stitcher.rib_count}")
assert stitcher.task_id == "test_task"

print("  ✓ HorizontalStitch 测试通过!")
print()

# 测试3: 配置导入
print("【测试3】验证配置文件")
print("-" * 60)

from configs.postprocessor_config import HORIZONTAL_STITCH_CONFIG, SCORING_CONFIG

print(f"  HORIZONTAL_STITCH_CONFIG 导入成功")
print(f"    - rib_count: {HORIZONTAL_STITCH_CONFIG['rib_count']}")
print(f"    - symmetry_type: {HORIZONTAL_STITCH_CONFIG['symmetry_type']}")
assert HORIZONTAL_STITCH_CONFIG['rib_count'] == 5

print(f"  SCORING_CONFIG 导入成功")
print(f"    - target_min: {SCORING_CONFIG['land_sea_ratio']['target_min']}")
print(f"    - target_max: {SCORING_CONFIG['land_sea_ratio']['target_max']}")
assert SCORING_CONFIG['land_sea_ratio']['target_min'] == 28.0

print("  ✓ 配置文件测试通过!")
print()

# 测试4: 服务层
print("【测试4】验证服务层集成")
print("-" * 60)

from services.postprocessor import _horizontal_stitch, _calculate_total_score

print("  _horizontal_stitch 导入成功")
print("  _calculate_total_score 导入成功")
print("  ✓ 服务层集成测试通过!")
print()

print("=" * 60)
print("✓ 所有集成测试通过!")
print("=" * 60)
