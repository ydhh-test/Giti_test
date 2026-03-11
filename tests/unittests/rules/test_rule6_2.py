# -*- coding: utf-8 -*-
"""
rule6_2 中间层单元测试
"""

import pytest
import shutil
from pathlib import Path
from PIL import Image

from rules.rule6_2 import (
    process_vertical_stitch,
    process_single_dir,
    _get_image_files,
    _aggregate_summary
)


class TestRule6_2:
    """rule6_2 中间层单元测试"""

    TEST_TASK_ID = "test_rule6_2"
    DATASET_BASE = Path("tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed")
    TEST_OUTPUT_BASE = Path(".results") / f"task_id_{TEST_TASK_ID}"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """测试准备和清理 - 每个测试前清理，最后一个测试后保留"""
        # 测试前清理并准备数据
        self._prepare_test_data()
        yield
        # 测试后不清理，保留输出目录用于验证

    def _prepare_test_data(self):
        """准备测试数据"""
        # 清理旧目录
        if self.TEST_OUTPUT_BASE.exists():
            shutil.rmtree(self.TEST_OUTPUT_BASE)

        # 创建目录结构
        self.TEST_OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

        # 复制测试数据到 filter 目录
        for filter_name in ["center_filter", "side_filter"]:
            src = self.DATASET_BASE / filter_name
            dst = self.TEST_OUTPUT_BASE / filter_name
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)

    # ========== 辅助函数测试 ==========

    def test_get_image_files(self):
        """测试图片文件获取和排序"""
        center_filter_dir = self.TEST_OUTPUT_BASE / "center_filter"
        image_files = _get_image_files(center_filter_dir)

        assert len(image_files) > 0
        assert all(f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']
                   for f in image_files)
        # 验证排序
        names = [f.name for f in image_files]
        assert names == sorted(names)

    def test_get_image_files_empty(self):
        """测试空目录"""
        empty_dir = self.TEST_OUTPUT_BASE / "empty_filter"
        empty_dir.mkdir(parents=True, exist_ok=True)

        image_files = _get_image_files(empty_dir)
        assert len(image_files) == 0

    def test_get_image_files_mixed_ext(self):
        """测试混合扩展名"""
        # 创建混合扩展名测试数据
        mixed_dir = self.TEST_OUTPUT_BASE / "mixed_filter"
        mixed_dir.mkdir(parents=True, exist_ok=True)

        # 创建不同扩展名的测试图片
        img = Image.new('RGB', (50, 50), color='red')
        img.save(mixed_dir / "test1.png", "PNG")
        img.save(mixed_dir / "test2.jpg", "JPEG")

        image_files = _get_image_files(mixed_dir)
        assert len(image_files) == 2
        extensions = set(f.suffix.lower() for f in image_files)
        assert '.png' in extensions
        assert '.jpg' in extensions

    def test_aggregate_summary(self):
        """测试统计聚合"""
        dir_stats = {
            "center_filter": {
                "total_count": 5,
                "processed_count": 5,
                "success_count": 4,
                "failed_count": 1,
                "skipped_count": 0
            },
            "side_filter": {
                "total_count": 3,
                "processed_count": 3,
                "success_count": 3,
                "failed_count": 0,
                "skipped_count": 0
            }
        }

        summary = _aggregate_summary(dir_stats)

        assert summary["total_images"] == 8
        assert summary["total_processed"] == 8
        assert summary["total_success"] == 7
        assert summary["total_failed"] == 1
        assert summary["total_skipped"] == 0

    # ========== 单目录处理测试 ==========

    def test_process_single_dir_center(self):
        """测试 center_filter 处理"""
        input_dir = self.TEST_OUTPUT_BASE / "center_filter"
        output_dir = self.TEST_OUTPUT_BASE / "center_vertical"

        flag, stats = process_single_dir(
            input_dir=input_dir,
            output_dir=output_dir,
            stitch_count=5,
            target_size=(200, 1241),
            task_id=self.TEST_TASK_ID,
            filter_dir="center_filter"
        )

        assert flag is True
        assert stats["total_count"] > 0
        assert stats["success_count"] == stats["total_count"]
        assert output_dir.exists()

        # 验证输出图片尺寸
        for img_name in ["2.png"]:
            output_path = output_dir / img_name
            if output_path.exists():
                img = Image.open(output_path)
                assert img.size == (200, 1241)

    def test_process_single_dir_side(self):
        """测试 side_filter 处理"""
        input_dir = self.TEST_OUTPUT_BASE / "side_filter"
        output_dir = self.TEST_OUTPUT_BASE / "side_vertical"

        flag, stats = process_single_dir(
            input_dir=input_dir,
            output_dir=output_dir,
            stitch_count=5,
            target_size=(400, 1241),
            task_id=self.TEST_TASK_ID,
            filter_dir="side_filter"
        )

        assert flag is True
        assert stats["total_count"] > 0
        assert stats["success_count"] == stats["total_count"]
        assert output_dir.exists()

        # 验证输出图片尺寸
        for img_name in ["0.png"]:
            output_path = output_dir / img_name
            if output_path.exists():
                img = Image.open(output_path)
                assert img.size == (400, 1241)

    def test_process_single_dir_empty(self):
        """测试空目录处理"""
        empty_dir = self.TEST_OUTPUT_BASE / "empty_filter"
        empty_dir.mkdir(parents=True, exist_ok=True)
        output_dir = self.TEST_OUTPUT_BASE / "empty_vertical"

        flag, stats = process_single_dir(
            input_dir=empty_dir,
            output_dir=output_dir,
            stitch_count=5,
            target_size=(200, 1241),
            task_id=self.TEST_TASK_ID,
            filter_dir="empty_filter"
        )

        assert flag is True
        assert stats["total_count"] == 0
        assert stats["success_count"] == 0

    def test_process_single_dir_missing_params(self):
        """测试缺少必需参数"""
        input_dir = self.TEST_OUTPUT_BASE / "center_filter"
        output_dir = self.TEST_OUTPUT_BASE / "center_vertical_test"

        # stitch_count=None 应该在调用前被检测到
        # 这里测试 process_vertical_stitch 层的参数校验
        conf = {
            "base_path": ".results",
            "filters": [
                {
                    "dir": "center_filter",
                    "stitch_count": None,  # 缺少必需参数
                    "resolution": [200, 1241]
                }
            ]
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True  # 整体成功，但该 filter 失败
        assert "center_filter" in details["directories"]
        assert "err_msg" in details["directories"]["center_filter"]

    # ========== 主入口测试 ==========

    def test_process_vertical_stitch_single_filter(self):
        """测试单 filter 处理"""
        conf = {
            "base_path": ".results",
            "filters": [
                {
                    "dir": "center_filter",
                    "stitch_count": 5,
                    "resolution": [200, 1241]
                }
            ],
            "output_dir_suffix": "_vertical"
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True
        assert "directories" in details
        assert "summary" in details
        assert "center_filter" in details["directories"]

    def test_process_vertical_stitch_empty_filters(self):
        """测试 filters 为空"""
        conf = {
            "base_path": ".results",
            "filters": []
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is False
        assert "err_msg" in details
        assert "filters 不能为空" in details["err_msg"]

    def test_process_vertical_stitch_missing_dir(self):
        """测试目录不存在"""
        conf = {
            "base_path": ".results",
            "filters": [
                {
                    "dir": "nonexistent_filter",
                    "stitch_count": 5,
                    "resolution": [200, 1241]
                }
            ]
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True  # 整体成功，但该目录被跳过
        assert "nonexistent_filter" in details["directories"]

    def test_process_vertical_stitch_missing_params(self):
        """测试 filter 缺少必需参数"""
        conf = {
            "base_path": ".results",
            "filters": [
                {
                    "dir": "center_filter",
                    "stitch_count": None,  # 缺少必需参数
                    "resolution": [200, 1241]
                }
            ]
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True
        assert "center_filter" in details["directories"]
        assert "err_msg" in details["directories"]["center_filter"]

    def test_process_vertical_stitch_custom_suffix(self):
        """测试自定义输出目录后缀"""
        conf = {
            "base_path": ".results",
            "filters": [
                {
                    "dir": "center_filter",
                    "stitch_count": 5,
                    "resolution": [200, 1241]
                }
            ],
            "output_dir_suffix": "_custom"
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True
        # 验证输出目录是 center_custom 而不是 center_vertical
        output_dir = self.TEST_OUTPUT_BASE / "center_custom"
        assert output_dir.exists()

    # ========== 错误处理测试 ==========

    def test_error_handling_corrupt_image(self):
        """测试损坏图片处理"""
        # 创建损坏的图片文件
        corrupt_dir = self.TEST_OUTPUT_BASE / "corrupt_filter"
        corrupt_dir.mkdir(parents=True, exist_ok=True)

        # 写入无效的 PNG 数据
        corrupt_file = corrupt_dir / "corrupt.png"
        corrupt_file.write_bytes(b"not a valid png file")

        output_dir = self.TEST_OUTPUT_BASE / "corrupt_vertical"

        flag, stats = process_single_dir(
            input_dir=corrupt_dir,
            output_dir=output_dir,
            stitch_count=5,
            target_size=(200, 1241),
            task_id=self.TEST_TASK_ID,
            filter_dir="corrupt_filter"
        )

        # 损坏图片应该被跳过，但不影响整体成功
        assert flag is True
        assert stats["failed_count"] == 1
        assert stats["images"]["corrupt.png"]["status"] == "failed"

    def test_error_handling_partial_failure(self):
        """测试部分失败场景"""
        # 创建混合数据：好图片 + 坏图片
        mixed_dir = self.TEST_OUTPUT_BASE / "partial_filter"
        mixed_dir.mkdir(parents=True, exist_ok=True)

        # 添加好图片
        good_img = Image.new('RGB', (50, 50), color='red')
        good_img.save(mixed_dir / "good.png", "PNG")

        # 添加坏图片
        corrupt_file = mixed_dir / "bad.png"
        corrupt_file.write_bytes(b"invalid png")

        output_dir = self.TEST_OUTPUT_BASE / "partial_vertical"

        flag, stats = process_single_dir(
            input_dir=mixed_dir,
            output_dir=output_dir,
            stitch_count=5,
            target_size=(200, 1241),
            task_id=self.TEST_TASK_ID,
            filter_dir="partial_filter"
        )

        assert flag is True
        assert stats["total_count"] == 2
        assert stats["success_count"] == 1
        assert stats["failed_count"] == 1

    # ========== 最终验证测试（最后执行，保留输出） ==========
    # 注意：方法名以 z_ 开头，确保在字母顺序中最后执行

    def test_z_process_vertical_stitch_multiple_filters(self):
        """测试多 filter 处理 - 最后执行，保留输出目录用于验证"""
        conf = {
            "base_path": ".results",
            "filters": [
                {
                    "dir": "center_filter",
                    "stitch_count": 5,
                    "resolution": [200, 1241]
                },
                {
                    "dir": "side_filter",
                    "stitch_count": 5,
                    "resolution": [400, 1241]
                }
            ],
            "output_dir_suffix": "_vertical"
        }

        flag, details = process_vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True
        assert "center_filter" in details["directories"]
        assert "side_filter" in details["directories"]

        # 验证输出目录存在
        center_output = self.TEST_OUTPUT_BASE / "center_vertical"
        side_output = self.TEST_OUTPUT_BASE / "side_vertical"
        assert center_output.exists()
        assert side_output.exists()

        # 验证输出图片尺寸
        center_img_path = center_output / "2.png"
        side_img_path = side_output / "0.png"

        if center_img_path.exists():
            img = Image.open(center_img_path)
            assert img.size == (200, 1241), f"center_vertical 输出尺寸应为 200x1241，实际为 {img.size}"

        if side_img_path.exists():
            img = Image.open(side_img_path)
            assert img.size == (400, 1241), f"side_vertical 输出尺寸应为 400x1241，实际为 {img.size}"
