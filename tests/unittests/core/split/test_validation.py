# -*- coding: utf-8 -*-

"""配置校验模块单元测试 - 覆盖所有valid/invalid场景
测试用例统计：
========================
4主沟情况（num_segments_to_remove=4）
  1. 正常输入（PASS）- 5个
     - [1, 2, 3, 4, 5] 保留全部
     - [1, 2, 3, 4] 保留side1, center2,3,4
     - [2, 3, 4, 5] 保留center2,3,4, side5
     - [1, 2] 保留side1, center2
     - [4, 5] 保留center4, side5
  2. 错误输入（FAIL）- 5个
     - [2, 3, 4] 缺少side索引
     - [1, 5] 缺少center索引
     - [1, 2, 2, 3] 包含重复值
     - [1, 2, 3, 4, 5, 6] 索引超出范围
     - [] 空列表

3主沟情况（num_segments_to_remove=3）
  1. 正常输入（PASS）- 3个
     - [1, 2, 3, 4] 保留全部
     - [1, 2, 3] 保留side1, center2,3
     - [2, 3, 4] 保留center2,3, side4
  2. 错误输入（FAIL）- 2个
     - [2, 3] 缺少side索引
     - [1, 4] 缺少center索引
========================
"""

import sys
import os
import unittest

from core.split.validation import _validate_vertical_parts_to_keep


# ===================== 4主沟情况（num_segments_to_remove=4） =====================

class TestValidateVerticalPartsToKeep_4Segments(unittest.TestCase):
    """num_segments_to_remove=4 场景下的校验测试"""

    # ========== 正常输入（PASS） ==========

    def test_valid_full_selection_1_2_3_4_5(self):
        """PASS: [1, 2, 3, 4, 5] 保留全部：side=[1,5], center=[2,3,4]"""
        _validate_vertical_parts_to_keep([1, 2, 3, 4, 5], num_segments_to_remove=4)

    def test_valid_1_2_3_4(self):
        """PASS: [1, 2, 3, 4] 保留side1, center2,3,4"""
        _validate_vertical_parts_to_keep([1, 2, 3, 4], num_segments_to_remove=4)

    def test_valid_2_3_4_5(self):
        """PASS: [2, 3, 4, 5] 保留center2,3,4, side5"""
        _validate_vertical_parts_to_keep([2, 3, 4, 5], num_segments_to_remove=4)

    def test_valid_1_2(self):
        """PASS: [1, 2] 保留side1, center2"""
        _validate_vertical_parts_to_keep([1, 2], num_segments_to_remove=4)

    def test_valid_4_5(self):
        """PASS: [4, 5] 保留center4, side5"""
        _validate_vertical_parts_to_keep([4, 5], num_segments_to_remove=4)

    # ========== 错误输入（FAIL） ==========

    def test_invalid_missing_side_2_3_4(self):
        """FAIL: [2, 3, 4] 缺少side索引"""
        with self.assertRaises(ValueError) as context:
            _validate_vertical_parts_to_keep([2, 3, 4], num_segments_to_remove=4)
        self.assertIn("必须至少包含一个side部分", str(context.exception))

    def test_invalid_missing_center_1_5(self):
        """FAIL: [1, 5] 缺少center索引"""
        with self.assertRaises(ValueError) as context:
            _validate_vertical_parts_to_keep([1, 5], num_segments_to_remove=4)
        self.assertIn("必须至少包含一个center部分", str(context.exception))

    def test_invalid_duplicate_1_2_2_3(self):
        """FAIL: [1, 2, 2, 3] 包含重复值"""
        with self.assertRaises(ValueError) as context:
            _validate_vertical_parts_to_keep([1, 2, 2, 3], num_segments_to_remove=4)
        self.assertIn("包含重复值", str(context.exception))

    def test_invalid_out_of_range_1_2_3_4_5_6(self):
        """FAIL: [1, 2, 3, 4, 5, 6] 索引超出范围"""
        with self.assertRaises(ValueError) as context:
            _validate_vertical_parts_to_keep([1, 2, 3, 4, 5, 6], num_segments_to_remove=4)
        self.assertIn("包含无效索引", str(context.exception))

    def test_invalid_empty_list(self):
        """FAIL: [] 空列表"""
        with self.assertRaises(ValueError) as context:
            _validate_vertical_parts_to_keep([], num_segments_to_remove=4)
        self.assertIn("不能为空列表", str(context.exception))


# ===================== 3主沟情况（num_segments_to_remove=3） =====================

class TestValidateVerticalPartsToKeep_3Segments(unittest.TestCase):
    """num_segments_to_remove=3 场景下的校验测试"""

    # ========== 正常输入（PASS） ==========

    def test_valid_full_selection_1_2_3_4(self):
        """PASS: [1, 2, 3, 4] 保留全部：side=[1,4], center=[2,3]"""
        _validate_vertical_parts_to_keep([1, 2, 3, 4], num_segments_to_remove=3)

    def test_valid_1_2_3(self):
        """PASS: [1, 2, 3] 保留side1, center2,3"""
        _validate_vertical_parts_to_keep([1, 2, 3], num_segments_to_remove=3)

    def test_valid_2_3_4(self):
        """PASS: [2, 3, 4] 保留center2,3, side4"""
        _validate_vertical_parts_to_keep([2, 3, 4], num_segments_to_remove=3)

    # ========== 错误输入（FAIL） ==========

    def test_invalid_missing_side_2_3(self):
        """FAIL: [2, 3] 缺少side索引"""
        with self.assertRaises(ValueError) as context:
            _validate_vertical_parts_to_keep([2, 3], num_segments_to_remove=3)
        self.assertIn("必须至少包含一个side部分", str(context.exception))

    def test_invalid_missing_center_1_4(self):
        """FAIL: [1, 4] 缺少center索引"""
        with self.assertRaises(ValueError) as context:
            _validate_vertical_parts_to_keep([1, 4], num_segments_to_remove=3)
        self.assertIn("必须至少包含一个center部分", str(context.exception))


if __name__ == '__main__':
    unittest.main()
