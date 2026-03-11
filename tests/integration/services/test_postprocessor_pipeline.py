# -*- coding: utf-8 -*-
"""
postprocessor 全流程集成测试

测试完整 9 阶段流程的端到端正确性
"""

import pytest
import shutil
from pathlib import Path
from unittest.mock import patch

from services.postprocessor import postprocessor

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


class TestFullPipelineIntegration:
    """全流程端到端集成测试"""

    TEST_TASK_ID = "test_full_pipeline"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_full_pipeline_with_mock_todos(self):
        """测试全流程 - 使用 Mock 处理 TODO 阶段"""
        user_conf = {
            "tire_design_width": 1000,
            "decoration_style": "simple",
            "vertical_stitch_conf": {
                "center_vertical": {"resolution": [1000, 2000]},
                "side_vertical": {"resolution": [1000, 2000]},
                "center_count": 3,
                "side_count": 2,
            }
        }

        with patch('services.postprocessor._small_image_score',
                   return_value=(True, {"image_gen_number": 2, "task_id": self.TEST_TASK_ID})):
            with patch('services.postprocessor._calculate_total_score',
                       return_value=(True, {"total_score": 85.0, "task_id": self.TEST_TASK_ID})):
                with patch('services.postprocessor._standard_input',
                           return_value=(True, {"image_gen_number": 1, "task_id": self.TEST_TASK_ID})):

                    flag, details = postprocessor(self.TEST_TASK_ID, user_conf)

                    assert flag is True
                    assert "image_gen_number" in details
                    assert details["task_id"] == self.TEST_TASK_ID

    def test_full_pipeline_empty_config(self):
        """测试全流程 - 空配置"""
        with patch('services.postprocessor._small_image_score',
                   return_value=(True, {"image_gen_number": 0, "task_id": self.TEST_TASK_ID})):
            with patch('services.postprocessor._calculate_total_score',
                       return_value=(True, {"total_score": 0, "task_id": self.TEST_TASK_ID})):
                with patch('services.postprocessor._standard_input',
                           return_value=(True, {"image_gen_number": 0, "task_id": self.TEST_TASK_ID})):

                    flag, details = postprocessor(self.TEST_TASK_ID, {})

                    assert flag is True


class TestFullPipelineEdgeCases:
    """全流程边界情况测试"""

    TEST_TASK_ID = "test_pipeline_edge"

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        prepare_task_integration_data(self.TEST_TASK_ID)
        yield
        cleanup_task_data(self.TEST_TASK_ID)

    def test_pipeline_with_json_config(self, tmp_path):
        """测试全流程 - JSON 配置文件输入"""
        import json

        json_path = tmp_path / "config.json"
        user_conf = {
            "tire_design_width": 1200,
            "decoration_style": "simple"
        }
        with open(json_path, 'w') as f:
            json.dump(user_conf, f)

        with patch('services.postprocessor._small_image_score',
                   return_value=(True, {"image_gen_number": 2, "task_id": self.TEST_TASK_ID})):
            with patch('services.postprocessor._calculate_total_score',
                       return_value=(True, {"total_score": 85.0, "task_id": self.TEST_TASK_ID})):
                with patch('services.postprocessor._standard_input',
                           return_value=(True, {"image_gen_number": 1, "task_id": self.TEST_TASK_ID})):

                    flag, details = postprocessor(self.TEST_TASK_ID, str(json_path))

                    assert flag is True
