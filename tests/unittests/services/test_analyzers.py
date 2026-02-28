import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from services.analyzers import detect_pattern_continuity
from utils.io_utils import load_image, ImageType


class TestPatternContinuity:
    """测试花纹连续性检测功能"""

    TEST_DATA_PATH = "tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/"

    def test_positive_case_1(self):
        """测试正例1：花纹不连续"""
        image_path = Path(self.TEST_DATA_PATH) / "1.png"
        image = load_image(image_path, ImageType.PNG)
        result = detect_pattern_continuity(image)
        assert result == True

    def test_positive_case_2(self):
        """测试正例2：花纹不连续"""
        image_path = Path(self.TEST_DATA_PATH) / "2.png"
        image = load_image(image_path, ImageType.PNG)
        result = detect_pattern_continuity(image)
        assert result == True

    def test_negative_case_1(self):
        """测试反例1：花纹连续"""
        image_path = Path(self.TEST_DATA_PATH) / "0.png"
        image = load_image(image_path, ImageType.PNG)
        result = detect_pattern_continuity(image)
        assert result == False
