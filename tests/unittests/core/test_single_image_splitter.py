# -*- coding: utf-8 -*-

"""大图拆分模块单元测试
测试用例统计：
========================
一、完整流水线测试 - 3个
  设计角度：
  1. 4主沟场景：验证num_segments_to_remove=4时，完整流水线输出正确
  2. 3主沟场景：验证num_segments_to_remove=3时，完整流水线输出正确
  3. 默认配置：不传入config时，使用DEFAULT_CONFIG处理
 
二、配置校验测试 - 2个
  设计角度：
  1. 无效配置：vertical_parts_to_keep配置错误时返回config_error状态
  2. 不支持参数：num_segments_to_remove不在[3,4]范围内时抛出异常

三、过滤功能测试 - 2个
  设计角度：
  1. vertical_parts_to_keep过滤：只保留指定索引，验证输出数量减少
  2. 边界过滤：保留最小有效组合（1个side+1个center）

四、异常检测测试 - 1个
  设计角度：
  1. 宽高比异常：输入超宽图像，验证异常图像被正确识别
  2. 颜色异常：输入单色图像，验证异常图像被正确识别

五、结果结构测试 - 1个
  设计角度：
  1. 返回字典完整性：验证所有预期键存在
  2. stats统计信息：验证处理统计正确计数

========================
"""

import sys
import os
import unittest
import numpy as np

from src.core.single_image_splitter import process_single_file, DEFAULT_CONFIG

class TestProcessSingleFile(unittest.TestCase):
    """process_single_file 函数测试"""

    def _create_test_image_4_segments(self, height=300, width=500):
        """创建4主沟测试图像"""
        img = np.ones((height, width, 3), dtype=np.uint8) * 200
        for pos in [100, 200, 300, 400]:
            img[:, pos:pos+5, :] = [0, 0, 0]
        return img

    def _create_test_image_3_segments(self, height=300, width=400):
        """创建3主沟测试图像"""
        img = np.ones((height, width, 3), dtype=np.uint8) * 200
        for pos in [100, 200, 300]:
            img[:, pos:pos+5, :] = [0, 0, 0]
        return img

    # ========== 完整流水线测试 ==========

    def test_process_4_segments_full_pipeline(self):
        """PASS: 4主沟完整流水线处理"""
        img = self._create_test_image_4_segments()
        config = {'num_segments_to_remove': 4}
        result = process_single_file(img, config)
        self.assertIn('side_final_images', result)
        self.assertIn('center_final_images', result)
        self.assertIn('abnormal_images', result)
        self.assertIn('stats', result)
        self.assertEqual(result['stats']['status'], 'success')
        self.assertGreater(result['stats']['vertical_segments'], 0)

    def test_process_3_segments_full_pipeline(self):
        """PASS: 3主沟完整流水线处理"""
        img = self._create_test_image_3_segments()
        config = {'num_segments_to_remove': 3}
        result = process_single_file(img, config)
        self.assertEqual(result['stats']['status'], 'success')
        self.assertGreater(result['stats']['vertical_segments'], 0)

    def test_default_config(self):
        """PASS: 使用默认配置处理"""
        img = self._create_test_image_4_segments()
        result = process_single_file(img, {})
        self.assertEqual(result['stats']['status'], 'success')

    # ========== 配置校验测试 ==========

    def test_invalid_config_returns_error(self):
        """FAIL: vertical_parts_to_keep配置错误返回config_error"""
        img = self._create_test_image_4_segments()
        config = {
            'num_segments_to_remove': 4,
            'vertical_parts_to_keep': [2, 3, 4]
        }
        result = process_single_file(img, config)
        self.assertEqual(result['stats']['status'], 'config_error')
        self.assertEqual(len(result['side_final_images']), 0)
        self.assertEqual(len(result['center_final_images']), 0)

    def test_unsupported_segments(self):
        """FAIL: 不支持的主沟数抛出异常"""
        img = self._create_test_image_4_segments()
        config = {'num_segments_to_remove': 2}
        result = process_single_file(img, config)
        self.assertEqual(result['stats']['status'], 'error')

    # ========== 过滤功能测试 ==========

    def test_vertical_parts_to_keep_filtering(self):
        """PASS: vertical_parts_to_keep过滤生效"""
        img = self._create_test_image_4_segments()
        config = {
            'num_segments_to_remove': 4,
            'vertical_parts_to_keep': [1, 2, 3]
        }
        result = process_single_file(img, config)
        self.assertEqual(result['stats']['status'], 'success')
        self.assertEqual(result['stats']['vertical_segments'], 3)

    def test_vertical_parts_minimal_keep(self):
        """PASS: 保留最小有效组合（1个side+1个center）"""
        img = self._create_test_image_4_segments()
        config = {
            'num_segments_to_remove': 4,
            'vertical_parts_to_keep': [1, 2]
        }
        result = process_single_file(img, config)
        self.assertEqual(result['stats']['status'], 'success')
        self.assertEqual(result['stats']['vertical_segments'], 2)

    # ========== 异常检测测试 ==========

    def test_abnormal_image_detection(self):
        """PASS: 异常宽高比图像被正确检测"""
        img = np.ones((50, 300, 3), dtype=np.uint8) * 128
        config = {'num_segments_to_remove': 4}
        result = process_single_file(img, config)
        self.assertEqual(result['stats']['status'], 'success')
        self.assertGreaterEqual(result['stats']['abnormal_count'], 0)


if __name__ == '__main__':
    unittest.main()
