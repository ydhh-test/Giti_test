import sys
import os
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from services.analyzers import detect_pattern_continuity
from utils.io_utils import load_image, ImageType


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
            task_id='task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed',
            image_type='center_inf',
            image_id='2'
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
        # 验证可视化保存路径
        assert details['visualization'] == 'tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/detect_pattern_continuity/center_inf/2.png'
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
            task_id='task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed',
            image_type='side_inf',
            image_id='0'
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
        # 验证可视化保存路径
        assert details['visualization'] == 'tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/detect_pattern_continuity/side_inf/0.png'
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
            task_id='task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed',
            image_type='center_inf',
            image_id='0'
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
        # 验证可视化保存路径
        assert details['visualization'] == 'tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/detect_pattern_continuity/center_inf/0.png'
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
            task_id='task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed',
            image_type='center_inf',
            image_id='1'
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
        # 验证可视化保存路径
        assert details['visualization'] == 'tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/detect_pattern_continuity/center_inf/1.png'
        # 花纹不连续
        assert details['is_continuous'] == False
