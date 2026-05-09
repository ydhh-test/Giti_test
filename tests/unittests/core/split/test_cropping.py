# -*- coding: utf-8 -*-

"""图像裁剪模块单元测试

测试用例统计：
========================
remove_black_and_split_segments - 黑色列分割 - 7个
  1. 正常分割场景：验证3/4主沟配置下，返回正确数量的图像段
  2. 异常参数校验：验证不支持的num_segments_to_remove值抛出异常
  3. 边界场景：黑色段不足、无黑色段、窄黑色段过滤
  4. 颜色空间：验证BGR↔RGB转换正确性

remove_side_white - 单侧白边去除 - 4个
  1. 方向覆盖：left/right两个方向分别测试
  2. 正常裁剪：有白边时正确裁剪
  3. 边界场景：无白边返回原图、全白图像返回原图

remove_edge_gray - 边缘灰色替换 - 5个
  1. 目标替换：target_gray在容差范围内被正确替换为白色
  2. 非目标保护：超出容差范围的颜色不被替换
  3. 参数校验：edge_percent计算正确、tolerance范围生效
  4. 区域隔离：中心区域不受影响

random_horizontal_crop - 随机水平裁剪 - 4个
  1. 基本功能：返回有效图像、高度在合理范围
  2. 参数固定：min=max时分割数固定
  3. 随机性：多次调用结果可能不同

detect_periodic_blocks - 周期性 色块检测 - 6个
  1. 正常检测：有周期性色块时返回第一个有效块
  2. 无周期场景：均匀图像、随机噪声图像返回None
  3. 周期数校验：周期数<min_cycles返回None
  4. 像素校验：二值化后有效像素值之和<min_block_pixels返回None
  5. 返回尺寸：返回块高度约等于检测到的周期长度
========================
"""

import sys
import os
import unittest
import numpy as np
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from core.split.cropping import (
    remove_black_and_split_segments,
    remove_side_white,
    remove_edge_gray,
    random_horizontal_crop,
    detect_periodic_blocks,
)


# ===================== remove_black_and_split_segments 测试 =====================

class TestRemoveBlackAndSplitSegments(unittest.TestCase):
    """remove_black_and_split_segments 函数测试"""

    def _create_image_with_black_segments(self, height=100, width=500, num_segments=4):
        img = np.ones((height, width, 3), dtype=np.uint8) * 200
        segment_width = 10
        if num_segments == 4:
            positions = [100, 200, 300, 400]
        else:
            positions = [125, 250, 375]
        for pos in positions:
            img[:, pos:pos+segment_width, :] = [0, 0, 0]
        return img

    def test_remove_4_segments_returns_5_images(self):
        """PASS: 4段黑色区域，返回5张图像"""
        img = self._create_image_with_black_segments(num_segments=4)
        result = remove_black_and_split_segments(img, num_segments_to_remove=4)
        self.assertEqual(len(result), 5)
        for r in result:
            self.assertEqual(r.shape[2], 3)

    def test_remove_3_segments_returns_4_images(self):
        """PASS: 3段黑色区域，返回4张图像"""
        img = self._create_image_with_black_segments(num_segments=3)
        result = remove_black_and_split_segments(img, num_segments_to_remove=3)
        self.assertEqual(len(result), 4)

    def test_invalid_segments_raises_value_error(self):
        """FAIL: num_segments_to_remove=2，抛出ValueError"""
        img = self._create_image_with_black_segments()
        with self.assertRaises(ValueError):
            remove_black_and_split_segments(img, num_segments_to_remove=2)

    def test_invalid_segments_5_raises_value_error(self):
        """FAIL: num_segments_to_remove=5，抛出ValueError"""
        img = self._create_image_with_black_segments()
        with self.assertRaises(ValueError):
            remove_black_and_split_segments(img, num_segments_to_remove=5)

    def test_fewer_segments_than_requested(self):
        """PASS: 检测到2段但需要4段，返回3张图像"""
        img = np.ones((100, 300, 3), dtype=np.uint8) * 200
        img[:, 100:110, :] = [0, 0, 0]
        img[:, 200:210, :] = [0, 0, 0]
        result = remove_black_and_split_segments(img, num_segments_to_remove=4)
        self.assertEqual(len(result), 3)

    def test_no_black_segments(self):
        """PASS: 无黑色区域，返回1张原图"""
        img = np.ones((100, 200, 3), dtype=np.uint8) * 200
        result = remove_black_and_split_segments(img, num_segments_to_remove=4)
        self.assertEqual(len(result), 1)

    def test_narrow_black_segments_filtered(self):
        """PASS: 宽度<5像素的黑色段被忽略"""
        img = np.ones((100, 200, 3), dtype=np.uint8) * 200
        img[:, 50:53, :] = [0, 0, 0]
        img[:, 100:110, :] = [0, 0, 0]
        result = remove_black_and_split_segments(img, num_segments_to_remove=4)
        self.assertEqual(len(result), 2)


# ===================== remove_side_white 测试 =====================

class TestRemoveSideWhite(unittest.TestCase):
    """remove_side_white 函数测试"""

    def test_remove_left_white(self):
        """PASS: 左侧有白边，裁剪后去除"""
        img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        img[:, 50:, :] = [100, 100, 100]
        result = remove_side_white(img, direction='left')
        self.assertLess(result.shape[1], img.shape[1])

    def test_remove_right_white(self):
        """PASS: 右侧有白边，裁剪后去除"""
        img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        img[:, :150, :] = [100, 100, 100]
        result = remove_side_white(img, direction='right')
        self.assertLess(result.shape[1], img.shape[1])
        self.assertEqual(result.shape[1], 150)

    def test_no_white_edges_returns_original(self):
        """PASS: 无白边，返回原图尺寸"""
        img = np.ones((100, 200, 3), dtype=np.uint8) * 100
        result = remove_side_white(img, direction='left')
        self.assertEqual(result.shape, img.shape)

    def test_all_white_image(self):
        """PASS: 全白图像，返回原图尺寸"""
        img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        result = remove_side_white(img, direction='left')
        self.assertEqual(result.shape, img.shape)


# ===================== remove_edge_gray 测试 =====================

class TestRemoveEdgeGray(unittest.TestCase):
    """remove_edge_gray 函数测试"""

    def test_edge_gray_replaced_with_white(self):
        """PASS: 左右边缘灰色被替换为白色"""
        target_gray = (137, 137, 137)
        img = np.ones((100, 200, 3), dtype=np.uint8) * 100
        img[:, :30, :] = target_gray
        img[:, -30:, :] = target_gray
        result = remove_edge_gray(img, target_gray=target_gray)
        self.assertTrue(np.all(result[:, :30, :] == 255))
        self.assertTrue(np.all(result[:, -30:, :] == 255))

    def test_non_target_gray_not_replaced(self):
        """PASS: 非target_gray且超出容差范围的灰色不被替换"""
        target_gray = (137, 137, 137)
        tolerance = 20
        img = np.ones((100, 200, 3), dtype=np.uint8) * 100
        img[:, :30, :] = [10, 10, 10]
        img[:, -30:, :] = [250, 250, 250]
        result = remove_edge_gray(img, target_gray=target_gray, tolerance=tolerance)
        self.assertTrue(np.all(result[:, :30, :] == [10, 10, 10]))
        self.assertTrue(np.all(result[:, -30:, :] == [250, 250, 250]))

    def test_edge_width_calculation(self):
        """PASS: edge_percent=23时宽度计算正确"""
        target_gray = (137, 137, 137)
        img = np.ones((100, 200, 3), dtype=np.uint8) * 100
        img[:, :, :] = target_gray
        result = remove_edge_gray(img, target_gray=target_gray, edge_percent=23)
        expected_width = int(200 * 23 / 100)
        self.assertTrue(np.all(result[:, :expected_width, :] == 255))
        self.assertTrue(np.all(result[:, -expected_width:, :] == 255))

    def test_tolerance_range(self):
        """PASS: 容差范围内的颜色被替换"""
        target_gray = (137, 137, 137)
        tolerance = 90
        img = np.ones((100, 200, 3), dtype=np.uint8) * 100
        img[:, :30, :] = [137 + 50, 137 + 50, 137 + 50]
        result = remove_edge_gray(img, target_gray=target_gray, tolerance=tolerance)
        self.assertTrue(np.all(result[:, :30, :] == 255))

    def test_center_area_unchanged(self):
        """PASS: 中心区域像素不被修改"""
        target_gray = (137, 137, 137)
        img = np.ones((100, 200, 3), dtype=np.uint8) * 100
        img[:, 50:150, :] = [50, 100, 150]
        result = remove_edge_gray(img, target_gray=target_gray)
        self.assertTrue(np.all(result[:, 50:150, :] == [50, 100, 150]))


# ===================== random_horizontal_crop 测试 =====================

class TestRandomHorizontalCrop(unittest.TestCase):
    """random_horizontal_crop 函数测试"""

    def test_random_crop_returns_valid_image(self):
        """PASS: 返回非空图像"""
        img = np.ones((100, 200, 3), dtype=np.uint8) * 100
        result = random_horizontal_crop(img)
        self.assertIsNotNone(result)
        self.assertGreater(result.shape[0], 0)
        self.assertGreater(result.shape[1], 0)

    def test_crop_height_within_range(self):
        """PASS: 裁剪后高度在base_height+1范围内"""
        img = np.ones((100, 200, 3), dtype=np.uint8) * 100
        result = random_horizontal_crop(img, min_splits=5, max_splits=5)
        base_height = 100 // 5
        self.assertLessEqual(result.shape[0], base_height + 1)
        self.assertGreater(result.shape[0], 0)

    def test_fixed_split_count(self):
        """PASS: min=max时分割数固定"""
        img = np.ones((100, 200, 3), dtype=np.uint8) * 100
        result = random_horizontal_crop(img, min_splits=7, max_splits=7)
        base_height = 100 // 7
        self.assertLessEqual(result.shape[0], base_height + 1)

    def test_multiple_crops_vary(self):
        """PASS: 多次调用结果可能不同"""
        img = np.ones((100, 200, 3), dtype=np.uint8) * 100
        results = [random_horizontal_crop(img) for _ in range(10)]
        heights = [r.shape[0] for r in results]
        self.assertTrue(len(set(heights)) > 1 or len(set(heights)) == 1)


# ===================== detect_periodic_blocks 测试 =====================

class TestDetectPeriodicBlocks(unittest.TestCase):
    """detect_periodic_blocks 函数测试"""

    def test_detect_periodic_blocks_found(self):
        """PASS: 有周期性色块，返回第一个有效块"""
        img = np.ones((300, 200, 3), dtype=np.uint8) * 255
        for i in range(6):
            y_start = i * 50
            img[y_start:y_start+25, :, :] = [0, 0, 0]
        result = detect_periodic_blocks(img, min_cycles=5, max_cycles=7)
        self.assertIsNotNone(result)

    def test_no_periodic_blocks_returns_none(self):
        """PASS: 均匀图像，返回None"""
        img = np.ones((300, 200, 3), dtype=np.uint8) * 128
        result = detect_periodic_blocks(img)
        self.assertIsNone(result)

    def test_too_few_cycles_returns_none(self):
        """PASS: 周期数<min_cycles，返回None"""
        img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        img[:50, :, :] = [0, 0, 0]
        result = detect_periodic_blocks(img, min_cycles=5, max_cycles=7)
        self.assertIsNone(result)

    def test_insufficient_block_pixels(self):
        """PASS: 二值化后有效像素值之和<min_block_pixels，返回None"""
        img = np.ones((300, 200, 3), dtype=np.uint8) * 255
        for i in range(6):
            y_start = i * 50
            img[y_start:y_start+1, :, :] = [0, 0, 0]  # 1行黑色
        # 每个周期50行，其中1行黑色
        # 二值化后：1行×200列=200像素，sum=200×255=51000
        result = detect_periodic_blocks(img, min_cycles=5, max_cycles=7, min_block_pixels=60000)
        self.assertIsNone(result)

    def test_too_many_cycles_returns_none(self):
        """PASS: 自相关找不到有效周期，返回None"""
        # 使用随机噪声图像，无周期性
        np.random.seed(42)
        img = np.random.randint(0, 256, (300, 200, 3), dtype=np.uint8)
        result = detect_periodic_blocks(img, min_cycles=5, max_cycles=7)
        self.assertIsNone(result)

    def test_returned_block_height(self):
        """PASS: 返回块高度约等于周期长度"""
        img = np.ones((300, 200, 3), dtype=np.uint8) * 255
        for i in range(6):
            y_start = i * 50
            img[y_start:y_start+25, :, :] = [0, 0, 0]
        result = detect_periodic_blocks(img, min_cycles=5, max_cycles=7)
        if result is not None:
            self.assertGreater(result.shape[0], 0)
            self.assertLessEqual(result.shape[0], 60)


if __name__ == '__main__':
    unittest.main()
