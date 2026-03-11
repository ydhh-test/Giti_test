# -*- coding: utf-8 -*-
"""
postprocessor 阶段集成测试

测试各阶段独立工作的正确性
"""

import pytest
import shutil
from pathlib import Path

from services.postprocessor import (
    postprocessor,
    _load_user_conf,
    _merge_conf_from_complete_config,
    _small_image_filter,
    _vertical_stitch,
    _horizontal_stitch,
    _horizontal_image_score,
    _add_decoration_borders,
)

# 项目根目录和测试数据目录
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_TEST_DATASETS_DIR = _PROJECT_ROOT / "tests" / "datasets" / "task_integration"
_RESULTS_DIR = _PROJECT_ROOT / ".results"


def prepare_task_integration_data(task_id: str) -> Path:
    """准备 task_integration 测试数据"""
    task_dir = _RESULTS_DIR / f"task_id_{task_id}"

    if task_dir.exists():
        shutil.rmtree(task_dir)

    task_dir.mkdir(parents=True, exist_ok=True)

    for inf_dir in ["center_inf", "side_inf"]:
        src = _TEST_DATASETS_DIR / inf_dir
        dst = task_dir / inf_dir
        if src.exists():
            shutil.copytree(src, dst)

    return task_dir


def cleanup_task_data(task_id: str):
    """清理任务测试数据"""
    task_dir = _RESULTS_DIR / f"task_id_{task_id}"
    if task_dir.exists():
        shutil.rmtree(task_dir)


class TestStage12Integration:
    """Stage 1-2 集成测试：Conf 处理 + 小图筛选"""

    TEST_TASK_ID = "test_stage12"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_conf_processing_with_dict(self):
        """测试 Conf 处理 - dict 输入"""
        user_conf = {"tire_design_width": 250}
        result = _load_user_conf(user_conf)
        assert result == user_conf

        merged = _merge_conf_from_complete_config(self.TEST_TASK_ID, user_conf)
        assert merged["tire_design_width"] == 250
        assert "vertical_stitch_conf" in merged

    def test_small_image_filter_integration(self):
        """测试小图筛选完整流程"""
        conf = {
            "filter_output_dirs": ["center_filter", "side_filter"],
            "pattern_continuity_conf": {
                "score": 10, "threshold": 200, "edge_height": 4,
                "coarse_threshold": 5, "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1, "connectivity": 4,
            },
            "visualize": True
        }

        flag, details = _small_image_filter(self.TEST_TASK_ID, conf)

        assert flag is True
        assert "image_gen_number" in details
        assert "pattern_continuity_stats" in details


class TestStage4Integration:
    """Stage 4 集成测试：纵图拼接"""

    TEST_TASK_ID = "test_stage4_vertical"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        from services.postprocessor import _small_image_filter
        _small_image_filter(self.TEST_TASK_ID, {
            "filter_output_dirs": ["center_filter", "side_filter"],
            "pattern_continuity_conf": {
                "score": 10, "threshold": 200, "edge_height": 4,
                "coarse_threshold": 5, "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1, "connectivity": 4,
            },
            "visualize": True
        })
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_vertical_stitch_integration(self):
        """测试纵图拼接完整流程"""
        conf = {
            "center_vertical": {"resolution": [1000, 2000]},
            "side_vertical": {"resolution": [1000, 2000]},
            "center_count": 3,
            "side_count": 2,
        }

        flag, details = _vertical_stitch(self.TEST_TASK_ID, conf)

        assert flag is True
        assert "directories" in details

        task_dir = _RESULTS_DIR / f"task_id_{self.TEST_TASK_ID}"
        assert (task_dir / "center_vertical").exists()
        assert (task_dir / "side_vertical").exists()


class TestStage5Integration:
    """Stage 5 集成测试：横图拼接"""

    TEST_TASK_ID = "test_stage5_horizontal"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        from services.postprocessor import _small_image_filter, _vertical_stitch
        _small_image_filter(self.TEST_TASK_ID, {
            "filter_output_dirs": ["center_filter", "side_filter"],
            "pattern_continuity_conf": {
                "score": 10, "threshold": 200, "edge_height": 4,
                "coarse_threshold": 5, "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1, "connectivity": 4,
            },
            "visualize": True
        })
        _vertical_stitch(self.TEST_TASK_ID, {
            "center_vertical": {"resolution": [1000, 2000]},
            "side_vertical": {"resolution": [1000, 2000]},
            "center_count": 3,
            "side_count": 2,
        })
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_horizontal_stitch_integration(self):
        """测试横图拼接完整流程"""
        from configs.user_config import DEFAULT_HORIZONTAL_STITCH_CONF

        flag, details = _horizontal_stitch(self.TEST_TASK_ID, DEFAULT_HORIZONTAL_STITCH_CONF)

        assert flag is True
        assert "directories" in details

        task_dir = _RESULTS_DIR / f"task_id_{self.TEST_TASK_ID}"
        assert (task_dir / "combine_horizontal").exists()


class TestStage67Integration:
    """Stage 6-7 集成测试：横图打分 + 装饰边框"""

    TEST_TASK_ID = "test_stage67"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        from services.postprocessor import _small_image_filter, _vertical_stitch, _horizontal_stitch
        from configs.user_config import DEFAULT_HORIZONTAL_STITCH_CONF

        _small_image_filter(self.TEST_TASK_ID, {
            "filter_output_dirs": ["center_filter", "side_filter"],
            "pattern_continuity_conf": {
                "score": 10, "threshold": 200, "edge_height": 4,
                "coarse_threshold": 5, "fine_match_distance": 4,
                "coarse_overlap_ratio": 0.67,
                "use_adaptive_threshold": False,
                "adaptive_method": "otsu",
                "min_line_width": 1, "connectivity": 4,
            },
            "visualize": True
        })
        _vertical_stitch(self.TEST_TASK_ID, {
            "center_vertical": {"resolution": [1000, 2000]},
            "side_vertical": {"resolution": [1000, 2000]},
            "center_count": 3,
            "side_count": 2,
        })
        _horizontal_stitch(self.TEST_TASK_ID, DEFAULT_HORIZONTAL_STITCH_CONF)
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_horizontal_image_score_integration(self):
        """测试横图打分完整流程"""
        from configs.user_config import DEFAULT_HORIZONTAL_IMAGE_SCORE_CONF

        flag, details = _horizontal_image_score(self.TEST_TASK_ID, DEFAULT_HORIZONTAL_IMAGE_SCORE_CONF)

        assert flag is True
        assert "image_gen_number" in details or "horizontal_image_score_stats" in details

    def test_add_decoration_borders_integration(self):
        """测试装饰边框完整流程"""
        decoration_conf = {
            "input_dir": "combine_horizontal",
            "output_dir": "combine",
            "tire_design_width": 1000,
            "decoration_style": "simple",
            "decoration_border_alpha": 0.5,
            "decoration_gray_color": [128, 128, 128],
        }

        flag, details = _add_decoration_borders(self.TEST_TASK_ID, decoration_conf)

        assert flag is True
        assert "image_gen_number" in details

        task_dir = _RESULTS_DIR / f"task_id_{self.TEST_TASK_ID}"
        assert (task_dir / "combine").exists()


class TestExceptionScenarios:
    """异常场景集成测试"""

    TEST_TASK_ID = "test_exceptions"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_invalid_user_conf_type(self):
        """测试异常：无效 user_conf 类型"""
        flag, details = postprocessor(self.TEST_TASK_ID, 12345)

        assert flag is False
        assert details["failed_stage"] == "conf_processing"
        assert "err_msg" in details

    def test_json_file_not_found(self):
        """测试异常：JSON 文件不存在"""
        flag, details = postprocessor(self.TEST_TASK_ID, "/non/existent/config.json")

        assert flag is False
        assert details["failed_stage"] == "conf_processing"

    def test_vertical_stitch_empty_config(self):
        """测试异常：纵图拼接空配置"""
        flag, details = _vertical_stitch(self.TEST_TASK_ID, {})

        assert flag is False
        assert "err_msg" in details

    def test_horizontal_stitch_empty_config(self):
        """测试异常：横图拼接空配置"""
        flag, details = _horizontal_stitch(self.TEST_TASK_ID, {})

        assert flag is False
        assert "err_msg" in details

    def test_stage_failure_propagation(self):
        """测试异常：阶段失败传播"""
        from unittest.mock import patch

        with patch('services.postprocessor._small_image_filter',
                   return_value=(False, {"err_msg": "Pattern continuity failed"})):

            flag, details = postprocessor(self.TEST_TASK_ID, {})

            assert flag is False
            assert details["failed_stage"] == "small_image_filter"
