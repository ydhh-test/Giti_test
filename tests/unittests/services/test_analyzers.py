import sys
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from services.analyzers import detect_pattern_continuity
from utils.io_utils import load_image, ImageType

# 测试配置
TEST_TASK_ID = "9f8d7b6a-5e4d-3c2b-1a09-876543210fed"
TEST_OUTPUT_BASE = ".results"


class TestPatternContinuity(unittest.TestCase):
    """测试花纹连续性检测功能"""

    def test_positive_case_0(self):
        """测试正例0：花纹连续
        测试数据：tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/2.png
        预期结果：连续 (score=10, is_continuous=True)"""
        image_path = Path("tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/2.png")
        image = load_image(image_path, ImageType.PNG)

        # 使用默认配置
        conf = {
            'score': 10,
            'threshold': 200,
            'edge_height': 4,
            'coarse_threshold': 5,
            'fine_match_distance': 4,
            'coarse_overlap_ratio': 0.67,
            'use_adaptive_threshold': False,
            'adaptive_method': 'otsu',
            'min_line_width': 1,
            'connectivity': 4,
            'vis_line_width': 2,
            'vis_font_scale': 0.5
        }

        # 添加可视化参数，保存图片到指定位置
        score, details = detect_pattern_continuity(
            image, conf,
            task_id=TEST_TASK_ID,
            image_type='center_inf',
            image_id='2',
            output_base_dir=TEST_OUTPUT_BASE
        )
        # 连续返回score为配置值
        assert score == 10
        # 验证details的结构
        assert 'is_continuous' in details
        assert 'top_ends' in details
        assert 'bottom_ends' in details
        assert 'matches' in details
        assert 'unmatched_top' in details
        assert 'unmatched_bottom' in details
        # 验证可视化保存路径（使用as_posix()确保跨平台兼容）
        expected_path = Path('.results').joinpath('task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed', 'center_mid_results', 'detect_pattern_continuity_2.png')
        assert details['visualization'] == expected_path.as_posix()
        # 花纹连续
        assert details['is_continuous'] == True

    def test_positive_case_1(self):
        """测试正例1：花纹连续
        测试数据：tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/side_inf/0.png
        预期结果：连续 (score=10, is_continuous=True)"""
        image_path = Path("tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/side_inf/0.png")
        image = load_image(image_path, ImageType.PNG)

        # 使用默认配置
        conf = {
            'score': 10,
            'threshold': 200,
            'edge_height': 4,
            'coarse_threshold': 5,
            'fine_match_distance': 4,
            'coarse_overlap_ratio': 0.67,
            'use_adaptive_threshold': False,
            'adaptive_method': 'otsu',
            'min_line_width': 1,
            'connectivity': 4,
            'vis_line_width': 2,
            'vis_font_scale': 0.5
        }

        # 添加可视化参数，保存图片到指定位置
        score, details = detect_pattern_continuity(
            image, conf,
            task_id=TEST_TASK_ID,
            image_type='side_inf',
            image_id='0',
            output_base_dir=TEST_OUTPUT_BASE
        )
        # 连续返回score为配置值
        assert score == 10
        # 验证details的结构
        assert 'is_continuous' in details
        assert 'top_ends' in details
        assert 'bottom_ends' in details
        assert 'matches' in details
        assert 'unmatched_top' in details
        assert 'unmatched_bottom' in details
        # 验证可视化保存路径（使用as_posix()确保跨平台兼容）
        expected_path = Path('.results').joinpath('task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed', 'side_mid_results', 'detect_pattern_continuity_0.png')
        assert details['visualization'] == expected_path.as_posix()
        # 花纹连续
        assert details['is_continuous'] == True

    def test_negative_case_0(self):
        """测试反例0：花纹不连续
        测试数据：tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/0.png
        预期结果：不连续 (score=0, is_continuous=False)"""
        image_path = Path("tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/0.png")
        image = load_image(image_path, ImageType.PNG)

        # 使用默认配置
        conf = {
            'score': 10,
            'threshold': 200,
            'edge_height': 4,
            'coarse_threshold': 5,
            'fine_match_distance': 4,
            'coarse_overlap_ratio': 0.67,
            'use_adaptive_threshold': False,
            'adaptive_method': 'otsu',
            'min_line_width': 1,
            'connectivity': 4,
            'vis_line_width': 2,
            'vis_font_scale': 0.5
        }

        # 添加可视化参数，保存图片到指定位置
        score, details = detect_pattern_continuity(
            image, conf,
            task_id=TEST_TASK_ID,
            image_type='center_inf',
            image_id='0',
            output_base_dir=TEST_OUTPUT_BASE
        )
        # 不连续返回score为0
        assert score == 0
        # 验证details的结构
        assert 'is_continuous' in details
        assert 'top_ends' in details
        assert 'bottom_ends' in details
        assert 'matches' in details
        assert 'unmatched_top' in details
        assert 'unmatched_bottom' in details
        # 验证可视化保存路径（使用as_posix()确保跨平台兼容）
        expected_path = Path('.results').joinpath('task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed', 'center_mid_results', 'detect_pattern_continuity_0.png')
        assert details['visualization'] == expected_path.as_posix()
        # 花纹不连续
        assert details['is_continuous'] == False

    def test_negative_case_1(self):
        """测试反例1：花纹不连续
        测试数据：tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/1.png
        预期结果：不连续 (score=0, is_continuous=False)"""
        image_path = Path("tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/1.png")
        image = load_image(image_path, ImageType.PNG)

        # 使用默认配置
        conf = {
            'score': 10,
            'threshold': 200,
            'edge_height': 4,
            'coarse_threshold': 5,
            'fine_match_distance': 4,
            'coarse_overlap_ratio': 0.67,
            'use_adaptive_threshold': False,
            'adaptive_method': 'otsu',
            'min_line_width': 1,
            'connectivity': 4,
            'vis_line_width': 2,
            'vis_font_scale': 0.5
        }

        # 添加可视化参数，保存图片到指定位置
        score, details = detect_pattern_continuity(
            image, conf,
            task_id=TEST_TASK_ID,
            image_type='center_inf',
            image_id='1',
            output_base_dir=TEST_OUTPUT_BASE
        )
        # 不连续返回0
        assert score == 0
        # 验证details的结构
        assert 'is_continuous' in details
        assert 'top_ends' in details
        assert 'bottom_ends' in details
        assert 'matches' in details
        assert 'unmatched_top' in details
        assert 'unmatched_bottom' in details
        # 验证可视化保存路径（使用as_posix()确保跨平台兼容）
        expected_path = Path('.results').joinpath('task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed', 'center_mid_results', 'detect_pattern_continuity_1.png')
        assert details['visualization'] == expected_path.as_posix()
        # 花纹不连续
        assert details['is_continuous'] == False


# ==========================================
# 海陆比测试 (从 tmp_dev_lxl 迁移)
# ==========================================
import pytest
import numpy as np
import cv2
import os

from services.analyzers import compute_land_sea_ratio, compute_black_area, compute_gray_area

# 测试数据路径
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets", "test_data_land_sea")
IMG_PATH_SCORE_2 = os.path.join(TEST_DATA_DIR, "2分.png")
ALL_WHITE_0 = os.path.join(TEST_DATA_DIR, "all_white.png")
MUCH_BLACK_0 = os.path.join(TEST_DATA_DIR, "much_blackLine.png")


@pytest.fixture
def default_conf():
    """提供测试用的标准评分配置"""
    return {
        "target_min": 28.0,
        "target_max": 35.0,
        "margin": 5.0
    }


def test_compute_black_area():
    """测试计算黑色区域面积"""
    img = np.full((10, 10), 255, dtype=np.uint8)
    img[0:3, 0:5] = 0
    assert compute_black_area(img) == 15


def test_compute_gray_area():
    """测试计算灰色区域面积"""
    img = np.full((10, 10), 255, dtype=np.uint8)
    img[0:5, 0:5] = 100
    assert compute_gray_area(img) == 25


def test_compute_land_sea_ratio_score_2_real_image(default_conf):
    """测试满分/容错情况：读取真实的业务图片"""
    img = cv2.imdecode(np.fromfile(IMG_PATH_SCORE_2, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert img is not None, f"错误：无法读取测试图片，请检查路径 -> {IMG_PATH_SCORE_2}"

    score, details = compute_land_sea_ratio(img, default_conf)
    print(f"\n[真实图片测试] 海陆比: {details['ratio_value']}%, 实际得分: {score}")

    # 海陆比 26.12% 在容差范围内，得 1 分
    assert score == 2, f"图片海陆比为 {details['ratio_value']}%，未在 28% ~ 35% 范围内"


def test_compute_land_sea_ratio_score_0_all_white(default_conf):
    """测试不合格情况：读取全白图片"""
    img = cv2.imdecode(np.fromfile(ALL_WHITE_0, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert img is not None, f"错误：无法读取测试图片，请检查路径 -> {ALL_WHITE_0}"

    score, details = compute_land_sea_ratio(img, default_conf)
    print(f"\n[全白图片测试] 海陆比: {details['ratio_value']}%, 应该得分: 0, 实际得分: {score}")

    assert score == 0, f"图片海陆比为 {details['ratio_value']}%，不符合 0 分标准"


def test_compute_land_sea_ratio_score_0_much_black(default_conf):
    """测试不合格情况：读取黑线图片"""
    img = cv2.imdecode(np.fromfile(MUCH_BLACK_0, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert img is not None, f"错误：无法读取测试图片，请检查路径 -> {MUCH_BLACK_0}"

    score, details = compute_land_sea_ratio(img, default_conf)
    print(f"\n[多黑线图片测试] 海陆比: {details['ratio_value']}%, 应该得分: 0, 实际得分: {score}")

    assert score == 0, f"图片海陆比为 {details['ratio_value']}%，不符合 0 分标准"
