# -*- coding: utf-8 -*-
"""
rule1to5 中间层单元测试

测试横图拼接中间层功能，包括正常流程和异常处理。
"""

import pytest
import shutil
from pathlib import Path

from rules.rule1to5 import process_horizontal_stitch


class TestRule1to5:
    """rule1to5 横图拼接中间层单元测试"""

    TEST_TASK_ID = "test_rule1to5"
    DATASET_BASE = Path("tests/datasets/task_id_test_rule1to5")
    TEST_OUTPUT_BASE = Path(".results") / f"task_id_{TEST_TASK_ID}"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """测试准备和清理"""
        # 测试前准备数据
        self._prepare_test_data()
        yield
        # 测试后不清理，保留正例输出

    def _prepare_test_data(self):
        """准备测试数据"""
        # 清理旧目录
        if self.TEST_OUTPUT_BASE.exists():
            shutil.rmtree(self.TEST_OUTPUT_BASE)

        # 创建目录结构
        self.TEST_OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

        # 复制测试数据到 center_vertical 和 side_vertical 目录
        for dir_name in ["center_vertical", "side_vertical"]:
            src = self.DATASET_BASE / dir_name
            dst = self.TEST_OUTPUT_BASE / dir_name
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)

    # ========== TC-01: 正常横图拼接流程 ==========

    def test_process_horizontal_stitch_success(self):
        """
        TC-01: 正常横图拼接流程

        场景：正常流程，有 center/side 图片
        配置：{"rib_count": 5, "symmetry_type": "both"}
        预期结果：flag=True, total_count=34, success_count=34, images=34
        清理策略：保留 combine_horizontal 目录（34 张图都保留）
        """
        conf = {
            "rib_count": 5,
            "symmetry_type": "both"
        }

        flag, result = process_horizontal_stitch(self.TEST_TASK_ID, conf)

        # 验证点
        assert flag is True, f"期望 flag=True, 实际 flag={flag}"
        assert result["task_id"] == self.TEST_TASK_ID, f"期望 task_id={self.TEST_TASK_ID}, 实际={result.get('task_id')}"

        # 验证统计信息
        stats = result["directories"]["combine_horizontal"]
        assert stats["total_count"] == 34, f"期望 total_count=34, 实际={stats['total_count']}"
        assert stats["success_count"] == 34, f"期望 success_count=34, 实际={stats['success_count']}"
        assert len(stats["images"]) == 34, f"期望 images 数量=34, 实际={len(stats['images'])}"

        # 验证实际文件存在且数量为 34
        combine_dir = self.TEST_OUTPUT_BASE / "combine_horizontal"
        assert combine_dir.exists(), "combine_horizontal 目录应该存在"
        actual_files = list(combine_dir.glob("*.png"))
        assert len(actual_files) == 34, f"期望实际文件数量=34, 实际={len(actual_files)}"

    # ========== TC-02: 空配置异常（已注释） ==========
    #
    # def test_process_horizontal_stitch_empty_conf(self):
    #     """
    #     TC-02: 空配置异常
    #
    #     场景：传入空配置 conf={}
    #     配置：{}
    #     预期结果：flag=False, err_msg 包含 "conf 不能为空"
    #     清理策略：清理临时文件（如有）
    #     """
    #     conf = {}
    #
    #     flag, result = process_horizontal_stitch(self.TEST_TASK_ID, conf)
    #
    #     # 验证点
    #     assert flag is False, f"期望 flag=False, 实际 flag={flag}"
    #     assert "task_id" in result, "结果应该包含 task_id"
    #     assert result["task_id"] == self.TEST_TASK_ID, f"期望 task_id={self.TEST_TASK_ID}, 实际={result.get('task_id')}"
    #     assert "err_msg" in result, "结果应该包含 err_msg"
    #     assert "conf 不能为空" in result["err_msg"], f"期望 err_msg 包含'conf 不能为空', 实际={result['err_msg']}"

    # ========== TC-03: 无图片异常（已注释） ==========
    #
    # def test_process_horizontal_stitch_no_images(self):
    #     """
    #     TC-03: 无图片异常
    #
    #     场景：center/side 目录为空
    #     配置：{"rib_count": 5, "symmetry_type": "both"}
    #     预期结果：flag=False, err_msg 包含 "图片加载失败"
    #     清理策略：清理临时文件（如有）
    #     """
    #     # 创建空的 center_vertical 和 side_vertical 目录
    #     empty_base = Path(".results") / f"task_id_{self.TEST_TASK_ID}_empty"
    #     if empty_base.exists():
    #         shutil.rmtree(empty_base)
    #     empty_base.mkdir(parents=True, exist_ok=True)
    #     (empty_base / "center_vertical").mkdir(parents=True, exist_ok=True)
    #     (empty_base / "side_vertical").mkdir(parents=True, exist_ok=True)
    #
    #     conf = {
    #         "rib_count": 5,
    #         "symmetry_type": "both",
    #         "base_path": ".results"
    #     }
    #
    #     # 使用空目录的 task_id
    #     empty_task_id = f"{self.TEST_TASK_ID}_empty"
    #     flag, result = process_horizontal_stitch(empty_task_id, conf)
    #
    #     # 验证点
    #     assert flag is False, f"期望 flag=False, 实际 flag={flag}"
    #     assert "task_id" in result, "结果应该包含 task_id"
    #     assert result["task_id"] == empty_task_id, f"期望 task_id={empty_task_id}, 实际={result.get('task_id')}"
    #     assert "err_msg" in result, "结果应该包含 err_msg"
    #     assert "图片加载失败" in result["err_msg"], f"期望 err_msg 包含'图片加载失败', 实际={result['err_msg']}"
    #
    #     # 清理临时文件
    #     if empty_base.exists():
    #         shutil.rmtree(empty_base)
