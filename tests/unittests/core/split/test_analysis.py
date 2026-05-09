# -*- coding: utf-8 -*-

"""图像分析模块单元测试

测试用例统计：
========================
analyze_dominant_color - 主色调分析 - 9个
  1. 正常检测：图像包含在[lower_bound, upper_bound]范围内的颜色，返回该颜色
  2. 默认颜色：所有颜色超出范围时返回default_color
  3. 边界值：颜色值恰好等于lower_bound或upper_bound
  4. 颜色空间：BGR输入正确转换为RGB处理
  5. 多颜色场景：多种颜色时返回最高频且在范围内的颜色
  6. 极端场景：全白、全黑、单色图像

remove_vertical_lines_center - 中央竖直线去除 - 7个
  1. 正常检测：图像中央有竖直线时正确去除
  2. 未检测场景：无竖直线、竖直线在边缘区域、竖直线长度不足
  3. 保护机制：竖直线与其他线相交时保护交点
  4. 方向过滤：非竖直线（横线/斜线）不被处理
  5. 多线场景：多条竖直线同时处理

analyze_single_image_abnormalities - 单图异常分析 - 9个
  1. 正常图像：宽高比正常、颜色种类>=3，返回无异常
  2. 宽高比异常：宽/高>4 或 高/宽>4 时正确检测
  3. 颜色异常：颜色种类<3 时正确检测
  4. 组合异常：同时存在宽高比异常和颜色异常
  5. 边界值：宽高比=4、颜色种类=3 时不触发异常
========================
"""

import sys
import os
import unittest
import numpy as np
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from core.split.analysis import (
    analyze_dominant_color,
    remove_vertical_lines_center,
    analyze_single_image_abnormalities,
)


# ===================== analyze_dominant_color 测试 =====================

class TestAnalyzeDominantColor(unittest.TestCase):
    """analyze_dominant_color 函数测试"""

    def test_dominant_color_in_range(self):
        """PASS: 图像包含在[15, 240]范围内的颜色，返回该颜色"""
        img = np.full((100, 100, 3), 100, dtype=np.uint8)
        result = analyze_dominant_color(img)
        self.assertEqual(result, (100, 100, 100))

    def test_dominant_color_out_of_range_returns_default(self):
        """PASS: 所有颜色超出范围，返回default_color"""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:, :] = [10, 10, 10]
        result = analyze_dominant_color(img, lower_bound=15, upper_bound=240, default_color=(137, 137, 137))
        self.assertEqual(result, (137, 137, 137))

    def test_dominant_color_white_returns_default(self):
        """PASS: 全白图像(255,255,255)超出范围"""
        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        result = analyze_dominant_color(img)
        self.assertEqual(result, (137, 137, 137))

    def test_dominant_color_black_returns_default(self):
        """PASS: 全黑图像(0,0,0)低于范围"""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = analyze_dominant_color(img)
        self.assertEqual(result, (137, 137, 137))

    def test_dominant_color_multiple_returns_most_frequent(self):
        """PASS: 多种颜色时返回最高频且在范围内的颜色"""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:70, :] = [100, 100, 100]
        img[70:, :] = [200, 200, 200]
        result = analyze_dominant_color(img)
        self.assertEqual(result, (100, 100, 100))

    def test_dominant_color_bgr_to_rgb_conversion(self):
        """PASS: BGR输入正确转换为RGB处理"""
        img_bgr = np.zeros((100, 100, 3), dtype=np.uint8)
        img_bgr[:, :] = [100, 150, 200]
        result = analyze_dominant_color(img_bgr)
        self.assertEqual(result, (200, 150, 100))

    def test_dominant_color_single_color(self):
        """PASS: 图像只有一种颜色"""
        img = np.full((50, 50, 3), 128, dtype=np.uint8)
        result = analyze_dominant_color(img)
        self.assertEqual(result, (128, 128, 128))

    def test_dominant_color_boundary_lower(self):
        """PASS: 颜色值恰好等于lower_bound(15)"""
        img = np.full((100, 100, 3), 15, dtype=np.uint8)
        result = analyze_dominant_color(img, lower_bound=15, upper_bound=240)
        self.assertEqual(result, (15, 15, 15))

    def test_dominant_color_boundary_upper(self):
        """PASS: 颜色值恰好等于upper_bound(240)"""
        img = np.full((100, 100, 3), 240, dtype=np.uint8)
        result = analyze_dominant_color(img, lower_bound=15, upper_bound=240)
        self.assertEqual(result, (240, 240, 240))


# ===================== remove_vertical_lines_center 测试 =====================

class TestRemoveVerticalLinesCenter(unittest.TestCase):
    """remove_vertical_lines_center 函数测试"""

    def _create_test_image_with_vertical_line(self, height=200, width=200, line_x=100):
        img = np.ones((height, width, 3), dtype=np.uint8) * 255
        cv2.line(img, (line_x, 0), (line_x, height - 1), (0, 0, 0), 2)
        return img

    def _create_test_image_with_horizontal_line(self, height=200, width=200, line_y=100):
        img = np.ones((height, width, 3), dtype=np.uint8) * 255
        cv2.line(img, (0, line_y), (width - 1, line_y), (0, 0, 0), 2)
        return img

    def test_remove_vertical_lines_detected(self):
        """PASS: 图像中央有竖直线，返回处理后图像"""
        img = self._create_test_image_with_vertical_line()
        result = remove_vertical_lines_center(img)
        self.assertIsNotNone(result)
        self.assertEqual(result.shape, img.shape)

    def test_remove_vertical_lines_none_detected(self):
        """PASS: 无竖直线，返回None"""
        img = np.ones((200, 200, 3), dtype=np.uint8) * 255
        result = remove_vertical_lines_center(img)
        self.assertIsNone(result)

    def test_remove_vertical_lines_at_edges(self):
        """PASS: 竖直线在margin区域外，不被去除"""
        img = self._create_test_image_with_vertical_line(line_x=5)
        result = remove_vertical_lines_center(img, margin_ratio=0.1)
        self.assertIsNone(result)

    def test_remove_vertical_lines_preserves_intersections(self):
        """PASS: 竖直线与其他线相交，交点被保护"""
        img = np.ones((200, 200, 3), dtype=np.uint8) * 255
        cv2.line(img, (100, 0), (100, 199), (0, 0, 0), 2)
        cv2.line(img, (0, 100), (199, 100), (0, 0, 0), 2)
        result = remove_vertical_lines_center(img)
        self.assertIsNotNone(result)
        self.assertTrue(np.any(result[100, 100] == 0))

    def test_remove_vertical_lines_too_short(self):
        """PASS: 竖直线长度小于length_ratio，不被检测"""
        img = np.ones((200, 200, 3), dtype=np.uint8) * 255
        cv2.line(img, (100, 80), (100, 120), (0, 0, 0), 2)
        result = remove_vertical_lines_center(img, length_ratio=0.7)
        self.assertIsNone(result)

    def test_remove_vertical_lines_multiple(self):
        """PASS: 多条竖直线同时被处理"""
        img = np.ones((200, 200, 3), dtype=np.uint8) * 255
        cv2.line(img, (80, 0), (80, 199), (0, 0, 0), 2)
        cv2.line(img, (100, 0), (100, 199), (0, 0, 0), 2)
        cv2.line(img, (120, 0), (120, 199), (0, 0, 0), 2)
        result = remove_vertical_lines_center(img)
        self.assertIsNotNone(result)

    def test_remove_non_vertical_lines_ignored(self):
        """PASS: 横线/斜线不被去除"""
        img = self._create_test_image_with_horizontal_line()
        result = remove_vertical_lines_center(img)
        self.assertIsNone(result)


# ===================== analyze_single_image_abnormalities 测试 =====================

class TestAnalyzeSingleImageAbnormalities(unittest.TestCase):
    """analyze_single_image_abnormalities 函数测试"""

    def test_normal_image_no_abnormalities(self):
        """PASS: 正常图像，无异常"""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        is_abnormal, abnormalities = analyze_single_image_abnormalities(img)
        self.assertFalse(is_abnormal)
        self.assertEqual(len(abnormalities), 0)

    def test_abnormal_width_ratio(self):
        """PASS: 宽/高 > 4，返回宽高比异常"""
        img = np.random.randint(0, 255, (10, 100, 3), dtype=np.uint8)
        is_abnormal, abnormalities = analyze_single_image_abnormalities(img)
        self.assertTrue(is_abnormal)
        self.assertTrue(any("宽高比异常" in a for a in abnormalities))

    def test_abnormal_height_ratio(self):
        """PASS: 高/宽 > 4，返回宽高比异常"""
        img = np.random.randint(0, 255, (100, 10, 3), dtype=np.uint8)
        is_abnormal, abnormalities = analyze_single_image_abnormalities(img)
        self.assertTrue(is_abnormal)
        self.assertTrue(any("宽高比异常" in a for a in abnormalities))

    def test_abnormal_few_colors(self):
        """PASS: 颜色种类 < 3，返回颜色异常"""
        img = np.full((100, 100, 3), 128, dtype=np.uint8)
        is_abnormal, abnormalities = analyze_single_image_abnormalities(img)
        self.assertTrue(is_abnormal)
        self.assertTrue(any("颜色种类过少" in a for a in abnormalities))

    def test_abnormal_both_ratio_and_colors(self):
        """PASS: 同时存在宽高比异常和颜色过少"""
        img = np.full((10, 100, 3), 128, dtype=np.uint8)
        is_abnormal, abnormalities = analyze_single_image_abnormalities(img)
        self.assertTrue(is_abnormal)
        self.assertEqual(len(abnormalities), 2)

    def test_boundary_width_ratio_exactly_4(self):
        """PASS: 宽/高 = 4，不触发异常"""
        img = np.random.randint(0, 255, (25, 100, 3), dtype=np.uint8)
        is_abnormal, abnormalities = analyze_single_image_abnormalities(img)
        self.assertFalse(is_abnormal)

    def test_boundary_width_ratio_slightly_over_4(self):
        """PASS: 宽/高 = 4.01，触发异常"""
        img = np.random.randint(0, 255, (100, 401, 3), dtype=np.uint8)
        is_abnormal, abnormalities = analyze_single_image_abnormalities(img)
        self.assertTrue(is_abnormal)

    def test_boundary_colors_exactly_3(self):
        """PASS: 颜色种类 = 3，不触发异常"""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:33, :] = [100, 100, 100]
        img[33:66, :] = [150, 150, 150]
        img[66:, :] = [200, 200, 200]
        is_abnormal, abnormalities = analyze_single_image_abnormalities(img)
        self.assertFalse(is_abnormal)

    def test_boundary_colors_2(self):
        """PASS: 颜色种类 = 2，触发异常"""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:50, :] = [100, 100, 100]
        img[50:, :] = [200, 200, 200]
        is_abnormal, abnormalities = analyze_single_image_abnormalities(img)
        self.assertTrue(is_abnormal)


if __name__ == '__main__':
    unittest.main()
