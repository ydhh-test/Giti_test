# -*- coding: utf-8 -*-
"""
横向拼接算法单元测试（新架构 dev2）

测试目标：src.core.stitching.horizontal_stitch
主要变更：import 路径 algorithms.stitching.* → src.core.stitching.*
"""

import sys
import pathlib
import os
import pytest
import numpy as np

_ROOT = pathlib.Path(__file__).parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.core.stitching.horizontal_stitch import (
    HorizontalStitch,
    CombinationManager,
    LayoutResult,
)


def test_layout_result_fields():
    """LayoutResult 数据结构字段正确"""
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    result = LayoutResult(
        layout_image=img,
        applied_symmetry="mirror",
        shift_offset=0.0,
        rib_regions=[(0, 0, 100, 100)],
        layout_score=8.0,
        rib_combination=(0, 1, 2, 3, 4),
    )
    assert result.applied_symmetry == "mirror"
    assert result.layout_score == 8.0
    assert len(result.rib_regions) == 1
    assert result.layout_image.shape == (100, 200, 3)


def test_combination_manager_5_rib():
    """CombinationManager - 5 RIB 模式：对称/非对称组合非空"""
    center_imgs = [np.zeros((100, 100, 3)) for _ in range(3)]
    side_imgs   = [np.zeros((100, 100, 3)) for _ in range(2)]
    conf   = {"max_per_mode": 5, "history_file": ".results/data/test_hist5.json"}
    mgr    = CombinationManager(center_imgs, side_imgs, 5, conf)

    asym = mgr.asymmetric_combinations
    sym  = mgr.symmetry_combinations
    assert len(asym) > 0
    assert len(sym)  > 0

    selected = mgr.select_combinations_by_priority("asymmetric", count=3)
    assert len(selected) == 3


def test_combination_manager_4_rib():
    """CombinationManager - 4 RIB 模式：对称/非对称组合非空"""
    center_imgs = [np.zeros((100, 100, 3)) for _ in range(2)]
    side_imgs   = [np.zeros((100, 100, 3)) for _ in range(2)]
    conf  = {"max_per_mode": 5, "history_file": ".results/data/test_hist4.json"}
    mgr   = CombinationManager(center_imgs, side_imgs, 4, conf)

    assert len(mgr.asymmetric_combinations) > 0
    assert len(mgr.symmetry_combinations)   > 0


def test_horizontal_stitch_init():
    """HorizontalStitch 初始化字段正确"""
    conf = {
        "rib_count":    5,
        "symmetry_type": "asymmetric",
        "center_dir":   "tests/datasets/horizontal_stitch/center",
        "side_dir":     "tests/datasets/horizontal_stitch/side-de-gray",
        "output_dir":   ".results/test_output",
    }
    stitcher = HorizontalStitch("test_task", conf)
    assert stitcher.task_id      == "test_task"
    assert stitcher.rib_count    == 5
    assert stitcher.symmetry_type == "asymmetric"


@pytest.mark.integration
def test_horizontal_stitch_process_with_real_data():
    """完整横图拼接流程（真实数据，标记为 integration）"""
    import tempfile, shutil

    center_dir = "tests/datasets/horizontal_stitch/center"
    side_dir   = "tests/datasets/horizontal_stitch/side-de-gray"
    if not os.path.exists(center_dir) or not os.path.exists(side_dir):
        pytest.skip("测试数据不存在")

    temp_output = tempfile.mkdtemp()
    try:
        conf = {
            "rib_count": 5,
            "symmetry_type": "rotate180",
            "center_dir":   center_dir,
            "side_dir":     side_dir,
            "output_dir":   temp_output,
            "max_per_mode": 2,
            "blend_width":  10,
            "main_groove_width": 30,
            "center_size":  (200, 1241),
            "side_size":    (400, 1241),
            "history_file": os.path.join(temp_output, "history.json"),
        }
        stitcher = HorizontalStitch("test_integration", conf)
        flag, details = stitcher.process()

        if flag:
            assert details["generated_count"] > 0
            assert "symmetry_types" in details
            assert "average_score"  in details
            output_files = [f for f in os.listdir(temp_output) if f.endswith('.png')]
            assert len(output_files) > 0
    finally:
        shutil.rmtree(temp_output, ignore_errors=True)


@pytest.mark.integration
def test_horizontal_stitch_symmetry_types():
    """多种对称模式各自输出文件（integration）"""
    import tempfile, shutil

    center_dir = "tests/datasets/horizontal_stitch/center"
    side_dir   = "tests/datasets/horizontal_stitch/side-de-gray"
    if not os.path.exists(center_dir) or not os.path.exists(side_dir):
        pytest.skip("测试数据不存在")

    for sym_type in ["asymmetric", "rotate180", "mirror", "mirror_shifted"]:
        temp_output = tempfile.mkdtemp()
        try:
            conf = {
                "rib_count": 5,
                "symmetry_type": sym_type,
                "center_dir":   center_dir,
                "side_dir":     side_dir,
                "output_dir":   temp_output,
                "max_per_mode": 1,
                "blend_width":  10,
                "main_groove_width": 30,
                "center_size":  (200, 1241),
                "side_size":    (400, 1241),
            }
            stitcher = HorizontalStitch(f"test_{sym_type}", conf)
            flag, details = stitcher.process()
            if flag:
                assert details["generated_count"] > 0
        finally:
            shutil.rmtree(temp_output, ignore_errors=True)
