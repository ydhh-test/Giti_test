import cv2
import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from services.analyzers import detect_pattern_continuity

# 图片路径配置
TEST_DATA_PATH = "tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/"

def load_test_image(filename):
    """加载测试图片"""
    image_path = f"{TEST_DATA_PATH}{filename}"
    return cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

def test_positive_case_1():
    """测试正例1：花纹不连续"""
    image = load_test_image("1.png")
    result = detect_pattern_continuity(image)
    assert result == True

def test_positive_case_2():
    """测试正例2：花纹不连续"""
    image = load_test_image("2.png")
    result = detect_pattern_continuity(image)
    assert result == True

def test_negative_case_1():
    """测试反例1：花纹连续"""
    image = load_test_image("0.png")
    result = detect_pattern_continuity(image)
    assert result == False
