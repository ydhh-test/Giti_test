"""
核心图像操作算法单元测试
"""

import unittest
import numpy as np
import cv2
from src.core.operation.image_operation import (
    apply_single_rib_operation,
    apply_rib_operations_sequence,
    repeat_vertically,
    apply_opacity,
    horizontal_concatenate,
    overlay_decoration
)
from src.models.enums import RibOperation


class TestImageOperation(unittest.TestCase):
    """核心图像操作算法测试"""

    def setUp(self):
        """测试前准备"""
        self.test_image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        self.gray_image = np.ones((100, 100), dtype=np.uint8) * 128

    def test_apply_single_rib_operation_none(self):
        """测试NONE操作"""
        result = apply_single_rib_operation(self.test_image, RibOperation.NONE)
        np.testing.assert_array_equal(result, self.test_image)

    def test_apply_single_rib_operation_flip_lr(self):
        """测试FLIP_LR操作"""
        result = apply_single_rib_operation(self.test_image, RibOperation.FLIP_LR)
        expected = cv2.flip(self.test_image, 1)
        np.testing.assert_array_equal(result, expected)

    def test_apply_single_rib_operation_flip(self):
        """测试FLIP操作"""
        result = apply_single_rib_operation(self.test_image, RibOperation.FLIP)
        expected = cv2.rotate(self.test_image, cv2.ROTATE_180)
        np.testing.assert_array_equal(result, expected)

    def test_apply_single_rib_operation_resize_horizontal_2x(self):
        """测试RESIZE_HORIZONTAL_2X操作"""
        result = apply_single_rib_operation(self.test_image, RibOperation.RESIZE_HORIZONTAL_2X)
        self.assertEqual(result.shape[0], 100)  # 高度不变
        self.assertEqual(result.shape[1], 200)  # 宽度翻倍

    def test_apply_single_rib_operation_left_right(self):
        """测试LEFT和RIGHT操作"""
        # LEFT
        result_left = apply_single_rib_operation(self.test_image, RibOperation.LEFT)
        self.assertEqual(result_left.shape[1], 50)  # 宽度减半

        # RIGHT
        result_right = apply_single_rib_operation(self.test_image, RibOperation.RIGHT)
        self.assertEqual(result_right.shape[1], 50)  # 宽度减半

    def test_apply_single_rib_operation_fractions(self):
        """测试分数操作"""
        # LEFT_1_3
        result = apply_single_rib_operation(self.test_image, RibOperation.LEFT_1_3)
        expected_width = int(100 * 1/3)
        self.assertEqual(result.shape[1], expected_width)

        # RIGHT_1_3
        result = apply_single_rib_operation(self.test_image, RibOperation.RIGHT_1_3)
        start_col = int(100 * 2/3)
        expected_width = 100 - start_col
        self.assertEqual(result.shape[1], expected_width)

    def test_apply_rib_operations_sequence(self):
        """测试操作序列"""
        operations = (RibOperation.RESIZE_HORIZONTAL_2X, RibOperation.LEFT)
        result = apply_rib_operations_sequence(self.test_image, operations)

        # 原图100x100 → resize后200x100 → left后100x100
        self.assertEqual(result.shape[0], 100)
        self.assertEqual(result.shape[1], 100)

    def test_repeat_vertically(self):
        """测试纵向重复"""
        result = repeat_vertically(self.test_image, 3)
        self.assertEqual(result.shape[0], 300)  # 高度×3
        self.assertEqual(result.shape[1], 100)  # 宽度不变

    def test_apply_opacity(self):
        """测试透明度应用"""
        result = apply_opacity(self.test_image, 128)
        self.assertEqual(result.shape[2], 4)  # BGRA格式
        self.assertTrue(np.all(result[:, :, 3] == 128))  # alpha通道

    def test_horizontal_concatenate(self):
        """测试横向拼接"""
        images = [self.test_image, self.test_image]
        result = horizontal_concatenate(images)
        self.assertEqual(result.shape[0], 100)  # 高度不变
        self.assertEqual(result.shape[1], 200)  # 宽度翻倍

    def test_overlay_decoration(self):
        """测试装饰覆盖"""
        left_dec = np.ones((100, 50, 3), dtype=np.uint8) * 200
        right_dec = np.ones((100, 50, 3), dtype=np.uint8) * 50

        result = overlay_decoration(self.test_image, left_dec, right_dec)
        self.assertEqual(result.shape[0], 100)  # 高度不变
        self.assertEqual(result.shape[1], 200)  # 总宽度 = 50 + 100 + 50

    def test_error_cases(self):
        """测试错误情况"""
        # 测试空图像
        with self.assertRaises(ValueError):
            apply_single_rib_operation(None, RibOperation.NONE)

        with self.assertRaises(ValueError):
            apply_single_rib_operation(np.array([]), RibOperation.NONE)

        # 测试无效操作
        with self.assertRaises(RuntimeError):
            apply_single_rib_operation(self.test_image, "invalid_operation")

        # 测试无效重复次数
        with self.assertRaises(ValueError):
            repeat_vertically(self.test_image, 0)

        with self.assertRaises(ValueError):
            repeat_vertically(self.test_image, -1)

        # 测试无效透明度
        with self.assertRaises(ValueError):
            apply_opacity(self.test_image, -1)

        with self.assertRaises(ValueError):
            apply_opacity(self.test_image, 256)


if __name__ == '__main__':
    unittest.main()