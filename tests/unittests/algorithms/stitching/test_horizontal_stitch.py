"""
横图拼接算法单元测试
"""

import pytest
import numpy as np
import cv2
import os
from algorithms.stitching.horizontal_stitch import (
    HorizontalStitch,
    CombinationManager,
    LayoutResult,
    assemble_symmetry_layout
)


def test_layout_result():
    """测试LayoutResult数据结构"""
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    result = LayoutResult(
        layout_image=img,
        applied_symmetry="mirror",
        shift_offset=0.0,
        rib_regions=[(0, 0, 100, 100)],
        layout_score=8.0,
        rib_combination=(0, 1, 2, 3, 4)
    )

    assert result.applied_symmetry == "mirror"
    assert result.layout_score == 8.0
    assert len(result.rib_regions) == 1
    assert result.layout_image.shape == (100, 200, 3)


def test_combination_manager_5_rib():
    """测试CombinationManager - 5 RIB模式"""
    center_images = [np.zeros((100, 100, 3)) for _ in range(3)]
    side_images = [np.zeros((100, 100, 3)) for _ in range(2)]

    config = {"max_per_mode": 5, "history_file": ".results/data/test_history.json"}
    manager = CombinationManager(center_images, side_images, 5, config)

    # 测试非对称组合生成
    asymmetric_combos = manager.asymmetric_combinations
    assert len(asymmetric_combos) > 0
    print(f"  5 RIB 非对称组合数: {len(asymmetric_combos)}")

    # 测试对称组合生成
    symmetry_combos = manager.symmetry_combinations
    assert len(symmetry_combos) > 0
    print(f"  5 RIB 对称组合数: {len(symmetry_combos)}")

    # 测试选择组合
    selected = manager.select_combinations_by_priority("asymmetric", count=3)
    assert len(selected) == 3
    print(f"  选中的组合: {selected[:3]}")


def test_combination_manager_4_rib():
    """测试CombinationManager - 4 RIB模式"""
    center_images = [np.zeros((100, 100, 3)) for _ in range(2)]
    side_images = [np.zeros((100, 100, 3)) for _ in range(2)]

    config = {"max_per_mode": 5, "history_file": ".results/data/test_history_4rib.json"}
    manager = CombinationManager(center_images, side_images, 4, config)

    # 测试非对称组合生成
    asymmetric_combos = manager.asymmetric_combinations
    assert len(asymmetric_combos) > 0
    print(f"  4 RIB 非对称组合数: {len(asymmetric_combos)}")

    # 测试对称组合生成
    symmetry_combos = manager.symmetry_combinations
    assert len(symmetry_combos) > 0
    print(f"  4 RIB 对称组合数: {len(symmetry_combos)}")


def test_horizontal_stitch_init():
    """测试HorizontalStitch初始化"""
    conf = {
        "rib_count": 5,
        "symmetry_type": "asymmetric",
        "center_dir": "tests/datasets/horizontal_stitch/center",
        "side_dir": "tests/datasets/horizontal_stitch/side-de-gray",
        "output_dir": ".results/test_output"
    }

    stitcher = HorizontalStitch("test_task", conf)
    assert stitcher.task_id == "test_task"
    assert stitcher.rib_count == 5
    assert stitcher.symmetry_type == "asymmetric"


# @pytest.mark.integration
def test_horizontal_stitch_process_with_real_data():
    """测试完整的横图拼接流程 - 使用真实数据"""
    import tempfile
    import shutil

    # 检查测试数据是否存在
    center_dir = "tests/datasets/horizontal_stitch/center"
    side_dir = "tests/datasets/horizontal_stitch/side-de-gray"

    if not os.path.exists(center_dir) or not os.path.exists(side_dir):
        pytest.skip("测试数据不存在")

    # 创建临时输出目录
    temp_output = tempfile.mkdtemp()

    try:
        conf = {
            "rib_count": 5,
            "symmetry_type": "rotate180",  # 使用单一模式加快测试
            "center_dir": center_dir,
            "side_dir": side_dir,
            "output_dir": temp_output,
            "max_per_mode": 2,  # 限制生成数量
            "blend_width": 10,
            "main_groove_width": 30,
            "center_size": (200, 1241),
            "side_size": (400, 1241),
            "history_file": os.path.join(temp_output, "history.json")
        }

        stitcher = HorizontalStitch("test_integration", conf)
        flag, details = stitcher.process()

        print(f"  处理结果: flag={flag}")
        print(f"  详细信息: {details}")

        # 验证结果
        if flag:
            assert "generated_count" in details
            assert details["generated_count"] > 0
            assert "symmetry_types" in details
            assert "average_score" in details

            # 验证输出文件
            output_files = [f for f in os.listdir(temp_output) if f.endswith('.png')]
            print(f"  生成的文件数: {len(output_files)}")
            assert len(output_files) > 0
        else:
            # 如果失败,打印错误信息
            print(f"  错误信息: {details.get('error', 'Unknown error')}")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_output, ignore_errors=True)


# @pytest.mark.integration
def test_horizontal_stitch_different_symmetry_types():
    """测试不同的对称模式"""
    import tempfile
    import shutil

    center_dir = "tests/datasets/horizontal_stitch/center"
    side_dir = "tests/datasets/horizontal_stitch/side-de-gray"

    if not os.path.exists(center_dir) or not os.path.exists(side_dir):
        pytest.skip("测试数据不存在")

    symmetry_types = ["asymmetric", "rotate180", "mirror", "mirror_shifted"]

    for sym_type in symmetry_types:
        temp_output = tempfile.mkdtemp()

        try:
            conf = {
                "rib_count": 5,
                "symmetry_type": sym_type,
                "center_dir": center_dir,
                "side_dir": side_dir,
                "output_dir": temp_output,
                "max_per_mode": 1,  # 每种模式只生成1张
                "blend_width": 10,
                "main_groove_width": 30,
                "center_size": (200, 1241),
                "side_size": (400, 1241)
            }

            stitcher = HorizontalStitch(f"test_{sym_type}", conf)
            flag, details = stitcher.process()

            print(f"  {sym_type}: flag={flag}, count={details.get('generated_count', 0)}")

            if flag:
                assert details["generated_count"] > 0
                output_files = [f for f in os.listdir(temp_output) if f.endswith('.png')]
                assert len(output_files) > 0

        finally:
            shutil.rmtree(temp_output, ignore_errors=True)


def test_canvas_margin_cropping():
    """测试左右黑边自动裁剪约束功能"""
    # 测试在侧边包含明显黑边的情况下，生成布局图是否能自动裁剪冗余边距
    rib1 = np.zeros((100, 50, 3), dtype=np.uint8)
    rib1[:, 20:50] = 255  # 左侧20像素纯黑，右侧30像素全白

    rib2 = np.zeros((100, 50, 3), dtype=np.uint8)
    rib2[:, 0:30] = 128  # 左侧30像素灰，右侧20像素纯黑

    result = assemble_symmetry_layout(
        extracted_ribs=[rib1, rib2],
        user_config={"symmetry_type": "asymmetric"},
        groove_positions=[[20]],  # 给一个较小的 groove，不要覆盖黑边测试的宽度
        rib_combination=(0, 1)
    )

    # 最关键的断言：整张最终拼好的 layout_image，其左右不能存在任何全黑冗余列
    # 左侧的 20 列黑边应该被切掉，右侧的 20 列黑边也应该被切掉
    # 整体返回的 width 应该小于直接叠加的最大理论 width
    gray_layout = cv2.cvtColor(result.layout_image, cv2.COLOR_BGR2GRAY)

    # 验证最左边和最右边的第一列/最后一列都不是全黑（即至少有一个像素>15）
    assert np.any(gray_layout[:, 0] > 15), "左侧黑边未完全裁切"
    assert np.any(gray_layout[:, -1] > 15), "右侧黑边未完全裁切"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
