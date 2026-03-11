# -*- coding: utf-8 -*-
"""
rule6_1 单元测试
"""

import pytest
import shutil
from pathlib import Path
import uuid

from rules.rule6_1 import (
    process_pattern_continuity,
    process_pattern_continuity_single_dir,
    _get_image_files,
    _copy_images,
    _aggregate_summary,
    _build_vis_output_dir
)


class TestRule6_1:
    """rule6_1 测试类"""

    # 伪造的 UUID
    TEST_TASK_ID = "test_rule6_1"

    # 测试数据源
    DATASET_BASE = Path("tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed")

    # 测试输出目录
    TEST_OUTPUT_BASE = Path(".results") / f"task_id_{TEST_TASK_ID}"

    # 预期保留的图片
    EXPECTED_KEPT = {
        "center_filter": ["2.png"],
        "side_filter": ["0.png"]
    }

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """每个测试前的准备（测试后不清理，保留输出目录用于验证）"""
        # 测试前：清理并准备数据
        self._prepare_test_data()

        yield

        # 测试后：保留输出目录，不清理
        # self._cleanup_test_data()

    def _prepare_test_data(self):
        """准备测试数据"""
        # 清理旧目录
        if self.TEST_OUTPUT_BASE.exists():
            shutil.rmtree(self.TEST_OUTPUT_BASE)

        # 创建目录结构
        self.TEST_OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

        # 复制测试数据 (inf 目录)
        for inf_dir in ["center_inf", "side_inf"]:
            src = self.DATASET_BASE / inf_dir
            dst = self.TEST_OUTPUT_BASE / inf_dir
            if src.exists():
                shutil.copytree(src, dst)

    def _cleanup_test_data(self):
        """清理测试数据"""
        if self.TEST_OUTPUT_BASE.exists():
            shutil.rmtree(self.TEST_OUTPUT_BASE)

    # ========== 辅助函数测试 ==========

    def test_get_image_files(self):
        """测试图片文件获取"""
        center_inf_dir = self.TEST_OUTPUT_BASE / "center_inf"
        image_files = _get_image_files(center_inf_dir)

        assert len(image_files) > 0
        assert all(f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']
                   for f in image_files)
        # 验证排序
        names = [f.name for f in image_files]
        assert names == sorted(names)

    def test_copy_images(self):
        """测试图片复制"""
        src = self.TEST_OUTPUT_BASE / "center_inf"
        dst = self.TEST_OUTPUT_BASE / "center_filter_copy"

        _copy_images(src, dst)

        assert dst.exists()
        src_files = set(f.name for f in _get_image_files(src))
        dst_files = set(f.name for f in _get_image_files(dst))
        assert src_files == dst_files

    def test_aggregate_summary(self):
        """测试统计聚合"""
        dir_stats = {
            "center_filter": {
                "total_count": 5,
                "kept_count": 3,
                "deleted_count": 2,
                "total_score": 30
            },
            "side_filter": {
                "total_count": 4,
                "kept_count": 2,
                "deleted_count": 2,
                "total_score": 20
            }
        }

        summary = _aggregate_summary(dir_stats)

        assert summary["total_images"] == 9
        assert summary["total_kept"] == 5
        assert summary["total_deleted"] == 4
        assert summary["total_score"] == 50

    def test_build_vis_output_dir(self):
        """测试可视化输出目录构建"""
        vis_dir = _build_vis_output_dir(self.TEST_TASK_ID, "center_filter")
        expected = Path(".results") / f"task_id_{self.TEST_TASK_ID}" / "rule6_1" / "center"
        assert vis_dir == expected

    # ========== 主流程测试 ==========

    def test_process_pattern_continuity_single_dir_center(self):
        """测试单目录处理 - center_filter"""
        # 先复制数据到 filter 目录
        src = self.TEST_OUTPUT_BASE / "center_inf"
        dst = self.TEST_OUTPUT_BASE / "center_filter"
        _copy_images(src, dst)

        # 准备配置
        conf = {
            "pattern_continuity_conf": {
                "score": 10,
                "threshold": 200,
                "edge_height": 4,
                "coarse_threshold": 5,
                "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1,
                "connectivity": 4,
            },
            "visualize": True
        }

        # 调用函数
        flag, stats = process_pattern_continuity_single_dir(
            dir_path=dst,
            filter_dir="center_filter",
            task_id=self.TEST_TASK_ID,
            conf=conf
        )

        # 验证结果
        assert flag is True
        assert stats["total_count"] > 0
        assert stats["kept_count"] == 1  # 只有 2.png 保留
        assert stats["deleted_count"] == stats["total_count"] - 1

        # 验证保留的文件
        remaining_files = list(dst.glob("*.png"))
        remaining_names = set(f.name for f in remaining_files)
        assert remaining_names == {"2.png"}

    def test_process_pattern_continuity_single_dir_side(self):
        """测试单目录处理 - side_filter"""
        # 先复制数据到 filter 目录
        src = self.TEST_OUTPUT_BASE / "side_inf"
        dst = self.TEST_OUTPUT_BASE / "side_filter"
        _copy_images(src, dst)

        # 准备配置
        conf = {
            "pattern_continuity_conf": {
                "score": 10,
                "threshold": 200,
                "edge_height": 4,
                "coarse_threshold": 5,
                "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1,
                "connectivity": 4,
            },
            "visualize": True
        }

        # 调用函数
        flag, stats = process_pattern_continuity_single_dir(
            dir_path=dst,
            filter_dir="side_filter",
            task_id=self.TEST_TASK_ID,
            conf=conf
        )

        # 验证结果
        assert flag is True
        assert stats["kept_count"] == 1  # 只有 0.png 保留

        # 验证保留的文件
        remaining_files = list(dst.glob("*.png"))
        remaining_names = set(f.name for f in remaining_files)
        assert remaining_names == {"0.png"}

    def test_process_pattern_continuity_full(self):
        """测试完整流程 - 所有目录"""
        # 先复制数据到 filter 目录
        for inf_dir, filter_dir in [("center_inf", "center_filter"),
                                      ("side_inf", "side_filter")]:
            src = self.TEST_OUTPUT_BASE / inf_dir
            dst = self.TEST_OUTPUT_BASE / filter_dir
            _copy_images(src, dst)

        # 准备配置
        conf = {
            "filter_output_dirs": ["center_filter", "side_filter"],
            "pattern_continuity_conf": {
                "score": 10,
                "threshold": 200,
                "edge_height": 4,
                "coarse_threshold": 5,
                "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1,
                "connectivity": 4,
            },
            "visualize": True
        }

        # 调用函数
        flag, details = process_pattern_continuity(
            task_id=self.TEST_TASK_ID,
            conf=conf
        )

        # 验证结果
        assert flag is True
        assert "directories" in details
        assert "summary" in details

        # 验证统计
        summary = details["summary"]
        assert summary["total_kept"] == 2  # center 2.png + side 0.png
        assert summary["total_deleted"] == summary["total_images"] - 2

        # 验证最终文件
        center_filter = self.TEST_OUTPUT_BASE / "center_filter"
        side_filter = self.TEST_OUTPUT_BASE / "side_filter"

        center_remaining = set(f.name for f in center_filter.glob("*.png"))
        side_remaining = set(f.name for f in side_filter.glob("*.png"))

        assert center_remaining == {"2.png"}
        assert side_remaining == {"0.png"}

        # 验证可视化文件生成
        # rule6_1 传递 vis_output_dir 作为 output_base_dir
        # 算法保存到：{vis_output_dir}/task_id_{task_id}/{image_type}_mid_results/
        # 即：.results/task_id_test_test_rule6_1/rule6_1/center/task_id_test_test_rule6_1/center_filter_mid_results/
        vis_center = self.TEST_OUTPUT_BASE / "rule6_1" / "center" / f"task_id_{self.TEST_TASK_ID}" / "center_filter_mid_results"
        vis_side = self.TEST_OUTPUT_BASE / "rule6_1" / "side" / f"task_id_{self.TEST_TASK_ID}" / "side_filter_mid_results"

        assert vis_center.exists()
        assert vis_side.exists()
        assert len(list(vis_center.glob("detect_pattern_continuity_*.png"))) > 0
        assert len(list(vis_side.glob("detect_pattern_continuity_*.png"))) > 0
