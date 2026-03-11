# -*- coding: utf-8 -*-
"""
rule19 单元测试 - 装饰边框中间层
"""

import pytest
import shutil
import cv2
import numpy as np
from pathlib import Path

from rules.rule19 import (
    process_decoration_borders,
    process_single_image,
    _get_image_files,
    _aggregate_summary,
    _build_empty_result
)


class TestRule19:
    """rule19 测试类"""

    TEST_TASK_ID = "test_rule19"
    TEST_OUTPUT_BASE = Path(".results") / f"task_id_{TEST_TASK_ID}"
    DATASET_BASE = Path("tests/datasets/task_id_test_rule13")

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, request):
        """每个测试前的准备"""
        is_full_test = request.function.__name__ == "test_process_decoration_borders_full"

        if not is_full_test:
            self._cleanup_test_data()

        yield
        # 测试后不清理，便于手动验证

    def _cleanup_test_data(self):
        """清理测试数据"""
        if self.TEST_OUTPUT_BASE.exists():
            shutil.rmtree(self.TEST_OUTPUT_BASE)

    def _copy_test_data(self) -> int:
        """
        复制测试数据到输入目录
        从 tests/datasets/task_id_test_rule13/combine_horizontal/
        复制到 .results/task_id_test_rule19/combine_horizontal/
        """
        src_dir = self.DATASET_BASE / "combine_horizontal"
        dst_dir = self.TEST_OUTPUT_BASE / "combine_horizontal"

        if not src_dir.exists():
            return 0

        dst_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        for img_file in src_dir.glob("*.png"):
            shutil.copy2(str(img_file), str(dst_dir / img_file.name))
            count += 1

        return count

    # ========== 辅助函数测试 ==========

    def test_get_image_files(self):
        """测试图片文件获取"""
        test_dir = self.TEST_OUTPUT_BASE / "test_get_image_files"
        test_dir.mkdir(parents=True, exist_ok=True)

        # 创建测试图片文件
        for name in ["c.png", "a.png", "b.png"]:
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.imwrite(str(test_dir / name), img)

        image_files = _get_image_files(test_dir)

        assert len(image_files) == 3
        names = [f.name for f in image_files]
        assert names == ["a.png", "b.png", "c.png"]

    def test_aggregate_summary(self):
        """测试统计聚合"""
        image_results = [
            {"status": "success"},
            {"status": "success"},
            {"status": "failed"},
            {"status": "success"},
        ]

        summary = _aggregate_summary(image_results)

        assert summary["total_images"] == 4
        assert summary["total_processed"] == 3
        assert summary["total_failed"] == 1

    def test_build_empty_result(self):
        """测试空结果构建"""
        result = _build_empty_result("test_input")

        assert result["task_id"] is None
        assert result["summary"]["total_images"] == 0

    # ========== 边界情况测试 ==========

    def test_process_decoration_borders_nonexistent_dir(self):
        """测试输入目录不存在的情况"""
        conf = {
            "input_dir": "nonexistent_dir",
            "output_dir": "combine",
            "tire_design_width": 1000,
            "decoration_border_alpha": 0.5,
            "decoration_gray_color": (135, 135, 135),
            "output_base_dir": str(self.TEST_OUTPUT_BASE.parent)
        }

        flag, details = process_decoration_borders(self.TEST_TASK_ID, conf)

        assert flag is True
        assert details["summary"]["total_images"] == 0

    def test_process_decoration_borders_empty_dir(self):
        """测试输入目录为空的情况"""
        # 创建空目录
        empty_dir = self.TEST_OUTPUT_BASE / "empty_input"
        empty_dir.mkdir(parents=True, exist_ok=True)

        conf = {
            "input_dir": "empty_input",
            "output_dir": "combine",
            "tire_design_width": 1000,
            "decoration_border_alpha": 0.5,
            "decoration_gray_color": (135, 135, 135),
            "output_base_dir": str(self.TEST_OUTPUT_BASE.parent)
        }

        flag, details = process_decoration_borders(self.TEST_TASK_ID, conf)

        assert flag is True
        assert details["summary"]["total_images"] == 0

    # ========== 单图处理测试 ==========

    def test_process_single_image(self):
        """测试单张图片处理"""
        # 创建测试图片
        input_dir = self.TEST_OUTPUT_BASE / "test_single_input"
        input_dir.mkdir(parents=True, exist_ok=True)
        image_path = input_dir / "test_single.png"

        # 创建 1480x1241 测试图片 (与测试数据集尺寸一致)
        img = np.zeros((1241, 1480, 3), dtype=np.uint8)
        img[:, :] = [120, 120, 120]  # 灰色背景
        cv2.imwrite(str(image_path), img)

        output_dir = self.TEST_OUTPUT_BASE / "test_single_output"
        output_dir.mkdir(parents=True, exist_ok=True)

        conf = {
            "tire_design_width": 1000,
            "decoration_border_alpha": 0.5,
            "decoration_gray_color": (135, 135, 135)
        }

        flag, result = process_single_image(
            image_path=image_path,
            task_id=self.TEST_TASK_ID,
            conf=conf,
            image_id=0,
            output_dir=output_dir
        )

        assert flag is True
        assert result["status"] == "success"
        assert result["image_name"] == "test_single.png"

        # 验证输出文件存在
        assert Path(result["output_path"]).exists()

    # ========== 完整流程测试 ==========

    def test_process_decoration_borders_full(self):
        """
        完整流程测试 - 使用真实测试数据

        测试场景:
        - 从 tests/datasets/task_id_test_rule13/combine_horizontal/ 复制 3 张图片
        - 执行完整的装饰边框处理
        - 验证返回值、输出文件
        """
        # Step 0: 清理旧目录
        self._cleanup_test_data()

        # Step 1: 准备测试数据
        copied_count = self._copy_test_data()
        assert copied_count == 3, f"预期复制 3 张图片，实际复制 {copied_count} 张"

        # Step 2: 准备配置 (显式指定 tire_design_width)
        conf = {
            "input_dir": "combine_horizontal",
            "output_dir": "combine",
            "tire_design_width": 1000,  # 显式指定
            "decoration_border_alpha": 0.5,
            "decoration_gray_color": (135, 135, 135),
            "output_base_dir": str(self.TEST_OUTPUT_BASE.parent)
        }

        # Step 3: 调用函数
        flag, details = process_decoration_borders(self.TEST_TASK_ID, conf)

        # Step 4: 验证返回值结构
        assert flag is True
        assert "task_id" in details
        assert "directories" in details
        assert "summary" in details

        # Step 5: 验证统计信息
        summary = details["summary"]
        assert summary["total_images"] == 3
        assert summary["total_processed"] == 3
        assert summary["total_failed"] == 0

        # Step 6: 验证每张图片的处理结果
        images = details["directories"]["combine"]["images"]
        assert len(images) == 3

        for image_name, image_data in images.items():
            assert image_data["status"] == "success"
            assert "output_path" in image_data
            # 验证输出文件存在
            assert Path(image_data["output_path"]).exists()

        # Step 7: 打印调试信息
        print(f"\n=== 完整流程测试通过 ===")
        print(f"输出目录：{self.TEST_OUTPUT_BASE / 'combine'}")
        print(f"处理图片数：{summary['total_processed']}")
        for image_name, image_data in images.items():
            print(f"  {image_name}: {image_data['status']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
