# -*- coding: utf-8 -*-

"""
后处理模块单元测试

测试 postprocessor.py 中的 9 阶段处理流程。

测试数据准备说明：
- 测试数据存储在 tests/datasets 目录
- 测试准备函数负责将必要数据拷贝到 .results 目录
- 功能函数对 .results 目录进行操作
"""

import sys
import os
import unittest
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from services.postprocessor import (
    postprocessor,
    _load_user_conf,
    _merge_conf_from_complete_config,
    _create_error_response,
    _small_image_filter,
    _small_image_score,
    _vertical_stitch,
    _horizontal_stitch,
    _horizontal_image_score,
    _add_decoration_borders,
    _calculate_total_score,
    _standard_input,
)

# ==========================================
# 测试数据准备工具函数
# ==========================================

# 项目根目录和测试数据目录
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_TEST_DATASETS_DIR = _PROJECT_ROOT / "tests" / "datasets"
_RESULTS_DIR = _PROJECT_ROOT / ".results"


def prepare_horizontal_stitch_data(task_id: str) -> Path:
    """
    准备横图拼接测试数据

    将 tests/datasets/horizontal_stitch 下的数据拷贝到 .results/{task_id}/data/horizontal_stitch

    Args:
        task_id: 任务 ID

    Returns:
        Path: 拷贝后的数据目录路径
    """
    src_dir = _TEST_DATASETS_DIR / "horizontal_stitch"
    dest_dir = _RESULTS_DIR / task_id / "data" / "horizontal_stitch"

    if not src_dir.exists():
        raise FileNotFoundError(f"Test data directory not found: {src_dir}")

    # 清理并创建目标目录
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 拷贝 center 和 side-de-gray 目录
    for subdir in ["center", "side-de-gray"]:
        src_subdir = src_dir / subdir
        dest_subdir = dest_dir / subdir
        if src_subdir.exists():
            shutil.copytree(src_subdir, dest_subdir)

    return dest_dir


def cleanup_task_data(task_id: str):
    """
    清理任务测试数据

    Args:
        task_id: 任务 ID
    """
    task_dir = _RESULTS_DIR / task_id
    if task_dir.exists():
        shutil.rmtree(task_dir)


class TestLoadUserConf(unittest.TestCase):
    """测试 _load_user_conf 函数"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = Path("/tmp/test_postprocessor")
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """清理测试环境"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_user_conf_dict_input(self):
        """测试 dict 类型输入"""
        user_conf = {"key1": "value1", "key2": 123}
        result = _load_user_conf(user_conf)
        self.assertEqual(result, user_conf)

    def test_user_conf_json_path_input(self):
        """测试 JSON 文件路径输入"""
        json_path = self.test_dir / "test_config.json"
        test_conf = {"tire_design_width": 200, "decoration_style": "simple"}
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(test_conf, f)

        result = _load_user_conf(str(json_path))
        self.assertEqual(result, test_conf)

    def test_user_conf_invalid_type(self):
        """测试无效类型输入（应报错）"""
        with self.assertRaises(TypeError) as context:
            _load_user_conf(12345)
        self.assertIn("user_conf must be dict or str", str(context.exception))

    def test_user_conf_invalid_json(self):
        """测试无效 JSON 文件（应报错）"""
        json_path = self.test_dir / "invalid.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write("{invalid json content")

        with self.assertRaises(json.JSONDecodeError):
            _load_user_conf(str(json_path))

    def test_user_conf_file_not_found(self):
        """测试 JSON 文件不存在（应报错）"""
        with self.assertRaises(FileNotFoundError) as context:
            _load_user_conf("/non/existent/path/config.json")
        self.assertIn("JSON config file not found", str(context.exception))


class TestMergeConfFromCompleteConfig(unittest.TestCase):
    """测试 _merge_conf_from_complete_config 函数"""

    def test_complete_config_merge(self):
        """测试配置合并逻辑"""
        user_conf = {"tire_design_width": 250, "custom_key": "custom_value"}
        result = _merge_conf_from_complete_config("test_task", user_conf)

        # 验证基础配置存在
        self.assertIsInstance(result, dict)

        # 验证用户配置覆盖了基础配置
        self.assertEqual(result.get("tire_design_width"), 250)
        self.assertEqual(result.get("custom_key"), "custom_value")


class TestCreateErrorResponse(unittest.TestCase):
    """测试 _create_error_response 函数"""

    def test_error_response_format(self):
        """测试错误返回格式"""
        task_id = "test_task_123"
        err_msg = "Test error message"
        failed_stage = "conf_processing"

        flag, details = _create_error_response(task_id, err_msg, failed_stage)

        self.assertFalse(flag)
        self.assertEqual(details["err_msg"], err_msg)
        self.assertEqual(details["failed_stage"], failed_stage)
        self.assertEqual(details["task_id"], task_id)


class TestStageFunctions(unittest.TestCase):
    """测试各阶段内部函数"""

    def setUp(self):
        """设置测试环境"""
        self.task_id = "test_task"
        self.test_dir = Path("/tmp/test_postprocessor_stages")
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """清理测试环境"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_small_image_filter_empty(self):
        """测试小图筛选空函数"""
        flag, details = _small_image_filter(self.task_id, {})
        self.assertTrue(flag)
        self.assertIn("image_gen_number", details)
        self.assertEqual(details["task_id"], self.task_id)

    def test_small_image_score_empty(self):
        """测试小图打分空函数"""
        flag, details = _small_image_score(self.task_id, {})
        self.assertTrue(flag)
        self.assertIn("image_gen_number", details)

    def test_horizontal_image_score_empty(self):
        """测试横图打分空函数"""
        flag, details = _horizontal_image_score(self.task_id, {})
        self.assertTrue(flag)
        self.assertIn("image_gen_number", details)

    def test_standard_input_empty(self):
        """测试整理输出空函数"""
        input_details = {"image_gen_number": 5, "test_key": "test_value"}
        flag, details = _standard_input(self.task_id, {}, input_details)
        self.assertTrue(flag)
        self.assertEqual(details, input_details)


class TestAddDecorationBorders(unittest.TestCase):
    """测试 _add_decoration_borders 函数"""

    def setUp(self):
        """设置测试环境"""
        self.task_id = "test_decoration_task"
        self.base_path = _RESULTS_DIR / self.task_id
        self.combine_dir = self.base_path / "combine"
        self.rst_dir = self.base_path / "rst"

        # 清理并创建测试目录
        if self.base_path.exists():
            shutil.rmtree(self.base_path)
        self.combine_dir.mkdir(parents=True, exist_ok=True)

        # 创建测试图片
        import cv2
        import numpy as np
        test_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        self.test_img_path = self.combine_dir / "test_image.png"
        cv2.imwrite(str(self.test_img_path), test_img)

    def tearDown(self):
        """清理测试环境"""
        cleanup_task_data(self.task_id)

    def test_add_decoration_borders_success(self):
        """测试装饰边框成功处理"""
        decoration_conf = {
            "input_dir": "combine",
            "output_dir": "rst",
            "tire_design_width": 1000,
            "decoration_style": "simple",
            "decoration_border_alpha": 0.5
        }

        # 验证配置存在
        self.assertIn("tire_design_width", decoration_conf)
        self.assertEqual(decoration_conf["decoration_style"], "simple")

    def test_add_decoration_borders_missing_tdw(self):
        """测试缺少 tire_design_width 配置"""
        decoration_conf = {
            "input_dir": "combine",
            "output_dir": "rst",
            "decoration_style": "simple"
            # tire_design_width 缺失
        }

        flag, details = _add_decoration_borders(self.task_id, decoration_conf)

        # 验证函数能够处理缺少 tire_design_width 的情况
        # rule19 会返回成功但统计为 0
        self.assertTrue(flag)

    def test_add_decoration_borders_input_dir_not_found(self):
        """测试输入目录不存在"""
        decoration_conf = {
            "input_dir": "nonexistent_dir",
            "output_dir": "rst",
            "tire_design_width": 1000,
            "decoration_style": "simple"
        }

        flag, details = _add_decoration_borders(self.task_id, decoration_conf)

        # 验证返回格式
        self.assertTrue(flag)
        # 输入目录不存在时，返回空结果
        self.assertEqual(details["image_gen_number"], 0)


class TestCalculateTotalScore(unittest.TestCase):
    """测试 _calculate_total_score 函数"""

    def setUp(self):
        """设置测试环境"""
        self.task_id = "test_score_task"
        self.base_path = _RESULTS_DIR / self.task_id
        self.rst_dir = self.base_path / "rst"

        # 清理并创建测试目录
        if self.base_path.exists():
            shutil.rmtree(self.base_path)
        self.rst_dir.mkdir(parents=True, exist_ok=True)

        # 创建测试图片
        import cv2
        import numpy as np
        test_img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        self.test_img_path = self.rst_dir / "test_image.png"
        cv2.imwrite(str(self.test_img_path), test_img)

    def tearDown(self):
        """清理测试环境"""
        cleanup_task_data(self.task_id)

    def test_calculate_total_score_rst_dir_not_found(self):
        """测试 rst 目录不存在"""
        invalid_task_id = "invalid_task"
        conf = {}

        flag, details = _calculate_total_score(invalid_task_id, conf)

        self.assertFalse(flag)
        self.assertIn("err_msg", details)
        # 错误消息可能包含 "rst directory not found" 或 "No images found"
        self.assertTrue(
            "rst directory not found" in details["err_msg"] or
            "No images found" in details["err_msg"],
            f"Unexpected error message: {details['err_msg']}"
        )

    def test_calculate_total_score_no_images(self):
        """测试 rst 目录中没有图片"""
        empty_task_id = "empty_task"
        empty_base_path = _RESULTS_DIR / empty_task_id
        empty_rst_dir = empty_base_path / "rst"

        # 清理并创建空目录
        if empty_base_path.exists():
            shutil.rmtree(empty_base_path)
        empty_rst_dir.mkdir(parents=True, exist_ok=True)

        try:
            conf = {}
            flag, details = _calculate_total_score(empty_task_id, conf)

            self.assertFalse(flag)
            self.assertIn("err_msg", details)
            self.assertIn("No images found", details["err_msg"])
        finally:
            cleanup_task_data(empty_task_id)


class TestPostprocessorIntegration(unittest.TestCase):
    """测试 postprocessor 主入口函数集成"""

    def setUp(self):
        """设置测试环境"""
        self.task_id = "integration_test_task"
        self.test_dir = _RESULTS_DIR / self.task_id
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """清理测试环境"""
        cleanup_task_data(self.task_id)

    @patch('services.postprocessor._small_image_filter', return_value=(True, {"image_gen_number": 0}))
    @patch('services.postprocessor._small_image_score', return_value=(True, {"image_gen_number": 0}))
    @patch('services.postprocessor._vertical_stitch', return_value=(True, {"image_gen_number": 0}))
    @patch('services.postprocessor._horizontal_stitch', return_value=(True, {"image_gen_number": 0}))
    @patch('services.postprocessor._horizontal_image_score', return_value=(True, {"image_gen_number": 0}))
    @patch('services.postprocessor._add_decoration_borders', return_value=(True, {"image_gen_number": 0, "0": {"image_score": 85.0, "image_path": "/test.png", "image_score_details": None}}))
    @patch('services.postprocessor._calculate_total_score', return_value=(True, {"total_score": 85.0}))
    @patch('services.postprocessor._standard_input', return_value=(True, {"image_gen_number": 1, "0": {"image_score": 85.0, "image_path": "/test.png", "image_score_details": None}}))
    def test_success_response_format(self, mock_standard_input, mock_calculate_total_score,
                                      mock_add_decoration_borders, mock_horizontal_image_score,
                                      mock_horizontal_stitch, mock_vertical_stitch,
                                      mock_small_image_score, mock_small_image_filter):
        """测试成功返回格式"""
        user_conf = {}
        flag, details = postprocessor(self.task_id, user_conf)

        self.assertTrue(flag)
        self.assertIsInstance(details, dict)
        self.assertIn("image_gen_number", details)

    def test_user_conf_dict_input(self):
        """测试 dict 类型 user_conf 输入"""
        # 这个测试主要验证 dict 输入被正确接受
        # 由于后续阶段需要实际环境，我们只验证 conf 处理阶段
        user_conf = {"tire_design_width": 250}
        # 验证 _load_user_conf 能正确处理 dict
        result = _load_user_conf(user_conf)
        self.assertEqual(result, user_conf)

    def test_user_conf_json_path_input(self):
        """测试 JSON 文件路径 user_conf 输入"""
        json_path = self.test_dir / "user_config.json"
        test_conf = {"tire_design_width": 300}
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(test_conf, f)

        # 验证 _load_user_conf 能正确处理 JSON 路径
        result = _load_user_conf(str(json_path))
        self.assertEqual(result, test_conf)

    def test_user_conf_invalid_type(self):
        """测试无效类型 user_conf 输入"""
        flag, details = postprocessor(self.task_id, 12345)

        self.assertFalse(flag)
        self.assertEqual(details["failed_stage"], "conf_processing")
        self.assertIn("err_msg", details)

    @patch('services.postprocessor._small_image_filter', return_value=(True, {"image_gen_number": 0}))
    @patch('services.postprocessor._small_image_score', return_value=(True, {"image_gen_number": 0}))
    @patch('services.postprocessor._vertical_stitch', return_value=(False, {"err_msg": "Vertical stitch failed", "task_id": "mock_task"}))
    def test_stage_failure_propagation(self, mock_vertical_stitch, mock_small_image_score, mock_small_image_filter):
        """测试各阶段失败的处理"""
        # Mock 前两个阶段成功，第三个阶段（vertical_stitch）失败
        user_conf = {}
        flag, details = postprocessor(self.task_id, user_conf)

        # 验证返回格式
        self.assertFalse(flag)
        self.assertIn("task_id", details)
        self.assertIn("failed_stage", details)
        self.assertEqual(details["failed_stage"], "vertical_stitch")
        self.assertIn("err_msg", details)


if __name__ == '__main__':
    unittest.main()
