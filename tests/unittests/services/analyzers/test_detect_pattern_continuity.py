# -*- coding: utf-8 -*-

"""
图案连续性检测算法单元测试

包含两个测试类：
1. TestPatternContinuitySimple: 不依赖numpy和opencv的简化测试
2. TestPatternContinuity: 依赖numpy和opencv的完整测试
"""

# Copyright © 2026 云端辉鸿. All rights reserved.
# Author: 桂禹 <guiyu@cloudhuihong.com>
# AI Assistant: ClaudeCode (Claude Sonnet 4)

import unittest
from itertools import product


class TestPatternContinuitySimple(unittest.TestCase):
    """
    图案连续性检测算法简化测试（不依赖numpy和opencv）

    测试核心算法逻辑：
    - 端点提取逻辑
    - 匹配规则
    - 端点匹配算法
    """

    def test_extract_ends_fine_lines(self):
        """测试1：提取细线端点"""
        row = [255] * 20  # 背景
        row[5] = 0  # 深色像素在位置5
        row[10] = 0  # 深色像素在位置10
        row[15] = 0  # 深色像素在位置15

        ends = self._extract_ends_from_binary_row(row, threshold=200, min_line_width=1)
        expected = [(5, 5, 'fine'), (10, 10, 'fine'), (15, 15, 'fine')]
        self.assertEqual(ends, expected)

    def test_extract_ends_coarse_lines(self):
        """测试2：提取粗线端点"""
        row = [255] * 50
        for i in range(10, 20):
            row[i] = 0  # 粗线：宽度10像素

        ends = self._extract_ends_from_binary_row(row, threshold=200, min_line_width=1, coarse_threshold=5)
        expected = [(10, 19, 'coarse')]
        self.assertEqual(ends, expected)

    def test_extract_ends_mixed_lines(self):
        """测试3：混合细线和粗线"""
        row = [255] * 50
        row[5] = 0  # 细线
        row[25] = 0  # 细线
        row[45] = 0  # 细线
        for i in range(10, 20):
            row[i] = 0  # 粗线
        for i in range(30, 40):
            row[i] = 0  # 粗线

        ends = self._extract_ends_from_binary_row(row, threshold=200, min_line_width=1, coarse_threshold=5)
        expected = [(5, 5, 'fine'), (10, 19, 'coarse'), (25, 25, 'fine'), (30, 39, 'coarse'), (45, 45, 'fine')]
        self.assertEqual(ends, expected)

    def test_extract_ends_filter_noise(self):
        """测试4：过滤噪音"""
        row = [255] * 20
        row[5] = 0  # 有效细线
        row[6] = 0  # 连续的像素，形成宽度2的线条
        row[10] = 0  # 噪音（单独一个像素）

        ends = self._extract_ends_from_binary_row(row, threshold=200, min_line_width=2, coarse_threshold=5)
        expected = [(5, 5, 'fine')]  # 噪音被过滤，细线用中心点表示
        self.assertEqual(ends, expected)

    def test_can_match_fine_fine_success(self):
        """测试5：细线-细线匹配（成功）"""
        top = (20, 20, 'fine')
        bottom = (22, 22, 'fine')
        fine_match_distance = 4
        coarse_overlap_ratio = 0.67

        result = self._can_match(top, bottom, fine_match_distance, coarse_overlap_ratio)
        self.assertTrue(result)

    def test_can_match_fine_fine_fail(self):
        """测试6：细线-细线匹配（失败）"""
        top = (20, 20, 'fine')
        bottom = (25, 25, 'fine')
        fine_match_distance = 4
        coarse_overlap_ratio = 0.67

        result = self._can_match(top, bottom, fine_match_distance, coarse_overlap_ratio)
        self.assertFalse(result)

    def test_can_match_fine_coarse_success(self):
        """测试7：细线-粗线匹配（成功）"""
        top = (30, 30, 'fine')
        bottom = (25, 35, 'coarse')
        fine_match_distance = 4
        coarse_overlap_ratio = 0.67

        result = self._can_match(top, bottom, fine_match_distance, coarse_overlap_ratio)
        self.assertTrue(result)

    def test_can_match_coarse_fine_success(self):
        """测试8：粗线-细线匹配（成功）"""
        top = (25, 35, 'coarse')
        bottom = (30, 30, 'fine')
        fine_match_distance = 4
        coarse_overlap_ratio = 0.67

        result = self._can_match(top, bottom, fine_match_distance, coarse_overlap_ratio)
        self.assertTrue(result)

    def test_can_match_coarse_coarse_success(self):
        """测试9：粗线-粗线匹配（成功）"""
        top = (10, 20, 'coarse')
        bottom = (12, 22, 'coarse')
        fine_match_distance = 4
        coarse_overlap_ratio = 0.67

        result = self._can_match(top, bottom, fine_match_distance, coarse_overlap_ratio)
        self.assertTrue(result)

    def test_can_match_coarse_coarse_fail(self):
        """测试10：粗线-粗线匹配（失败）"""
        top = (10, 20, 'coarse')
        bottom = (25, 35, 'coarse')
        fine_match_distance = 4
        coarse_overlap_ratio = 0.67

        result = self._can_match(top, bottom, fine_match_distance, coarse_overlap_ratio)
        self.assertFalse(result)

    def test_match_ends_perfect_match(self):
        """测试11：完美匹配"""
        top_ends = [(20, 20, 'fine'), (50, 50, 'fine'), (80, 80, 'fine')]
        bottom_ends = [(20, 20, 'fine'), (50, 50, 'fine'), (80, 80, 'fine')]
        fine_match_distance = 4
        coarse_overlap_ratio = 0.67

        matches, unmatched_top, unmatched_bottom = self._match_ends(
            top_ends, bottom_ends, fine_match_distance, coarse_overlap_ratio
        )

        self.assertEqual(len(matches), 3)
        self.assertEqual(len(unmatched_bottom), 0)
        is_continuous = len(unmatched_bottom) == 0
        self.assertTrue(is_continuous)

    def test_match_ends_large_offset(self):
        """测试12：错位太大"""
        top_ends = [(20, 20, 'fine'), (50, 50, 'fine'), (80, 80, 'fine')]
        bottom_ends = [(25, 25, 'fine'), (55, 55, 'fine'), (85, 85, 'fine')]
        fine_match_distance = 4
        coarse_overlap_ratio = 0.67

        matches, unmatched_top, unmatched_bottom = self._match_ends(
            top_ends, bottom_ends, fine_match_distance, coarse_overlap_ratio
        )

        self.assertEqual(len(matches), 0)
        self.assertEqual(len(unmatched_bottom), 3)
        is_continuous = len(unmatched_bottom) == 0
        self.assertFalse(is_continuous)

    def test_match_ends_one_to_many(self):
        """测试13：一对多（粗线覆盖多细线）"""
        top_ends = [(10, 60, 'coarse')]
        bottom_ends = [(15, 15, 'fine'), (25, 25, 'fine'), (55, 55, 'fine')]
        fine_match_distance = 4
        coarse_overlap_ratio = 0.67

        matches, unmatched_top, unmatched_bottom = self._match_ends(
            top_ends, bottom_ends, fine_match_distance, coarse_overlap_ratio
        )

        self.assertEqual(len(matches), 3)
        self.assertEqual(len(unmatched_bottom), 0)
        is_continuous = len(unmatched_bottom) == 0
        self.assertTrue(is_continuous)

    def test_match_ends_count_mismatch(self):
        """测试14：端点数量不匹配"""
        top_ends = [(20, 20, 'fine'), (50, 50, 'fine'), (80, 80, 'fine')]
        bottom_ends = [(20, 20, 'fine'), (50, 50, 'fine')]
        fine_match_distance = 4
        coarse_overlap_ratio = 0.67

        matches, unmatched_top, unmatched_bottom = self._match_ends(
            top_ends, bottom_ends, fine_match_distance, coarse_overlap_ratio
        )

        self.assertEqual(len(matches), 2)
        self.assertEqual(len(unmatched_bottom), 0)
        is_continuous = len(unmatched_bottom) == 0
        self.assertTrue(is_continuous)

    def test_match_ends_empty_edges(self):
        """测试15：空边缘"""
        top_ends = []
        bottom_ends = []
        fine_match_distance = 4
        coarse_overlap_ratio = 0.67

        matches, unmatched_top, unmatched_bottom = self._match_ends(
            top_ends, bottom_ends, fine_match_distance, coarse_overlap_ratio
        )

        self.assertEqual(len(matches), 0)
        self.assertEqual(len(unmatched_bottom), 0)
        is_continuous = len(unmatched_bottom) == 0
        self.assertTrue(is_continuous)

    def test_match_ends_single_side_empty(self):
        """测试16：一侧空边缘"""
        top_ends = [(20, 20, 'fine'), (50, 50, 'fine')]
        bottom_ends = []
        fine_match_distance = 4
        coarse_overlap_ratio = 0.67

        matches, unmatched_top, unmatched_bottom = self._match_ends(
            top_ends, bottom_ends, fine_match_distance, coarse_overlap_ratio
        )

        self.assertEqual(len(matches), 0)
        self.assertEqual(len(unmatched_bottom), 0)
        is_continuous = len(unmatched_bottom) == 0
        self.assertTrue(is_continuous)

    # ============ 辅助方法 ============

    def _extract_ends_from_binary_row(self, row, threshold, min_line_width=1, coarse_threshold=5):
        """从二值行中提取端点"""
        binary = [pixel <= threshold for pixel in row]

        ends = []
        i = 0
        while i < len(binary):
            if binary[i]:  # 找到深色像素
                start_x = i
                # 找到区间结束位置
                while i < len(binary) and binary[i]:
                    i += 1
                end_x = i - 1

                # 计算宽度
                width = end_x - start_x + 1

                # 过滤噪音
                if width >= min_line_width:
                    # 判断粗细
                    line_type = 'coarse' if width >= coarse_threshold else 'fine'

                    # 粗线使用区间，细线使用中心点
                    if line_type == 'fine':
                        center_x = (start_x + end_x) // 2
                        ends.append((center_x, center_x, 'fine'))
                    else:
                        ends.append((start_x, end_x, 'coarse'))
            else:
                i += 1

        return ends

    def _can_match(self, top_end, bottom_end, fine_match_distance, coarse_overlap_ratio):
        """判断两个端点是否可以匹配"""
        top_min_x, top_max_x, top_type = top_end
        bottom_min_x, bottom_max_x, bottom_type = bottom_end

        # 细线-细线匹配
        if top_type == 'fine' and bottom_type == 'fine':
            distance = abs(top_min_x - bottom_min_x)
            return distance <= fine_match_distance

        # 细线-粗线匹配
        if top_type == 'fine' and bottom_type == 'coarse':
            return bottom_min_x <= top_min_x <= bottom_max_x

        # 粗线-细线匹配
        if top_type == 'coarse' and bottom_type == 'fine':
            return top_min_x <= bottom_min_x <= top_max_x

        # 粗线-粗线匹配
        if top_type == 'coarse' and bottom_type == 'coarse':
            # 计算重合长度
            overlap_start = max(top_min_x, bottom_min_x)
            overlap_end = min(top_max_x, bottom_max_x)
            overlap_length = overlap_end - overlap_start + 1

            # 计算较短区间长度
            top_length = top_max_x - top_min_x + 1
            bottom_length = bottom_max_x - bottom_min_x + 1
            shorter_length = min(top_length, bottom_length)

            # 计算重合比例
            if shorter_length == 0:
                return False
            overlap_ratio = overlap_length / shorter_length

            return overlap_ratio >= coarse_overlap_ratio

        return False

    def _match_ends(self, top_ends, bottom_ends, fine_match_distance, coarse_overlap_ratio):
        """匹配上下边缘端点"""
        unmatched_bottom = set(range(len(bottom_ends)))
        matches = []

        # 全排列匹配
        for top_idx, bottom_idx in product(range(len(top_ends)), range(len(bottom_ends))):
            if bottom_idx in unmatched_bottom:
                if self._can_match(top_ends[top_idx], bottom_ends[bottom_idx], fine_match_distance, coarse_overlap_ratio):
                    unmatched_bottom.remove(bottom_idx)
                    matches.append((top_idx, bottom_idx))

        # 找出未匹配的上边缘
        matched_top = {top_idx for top_idx, _ in matches}
        unmatched_top = [i for i in range(len(top_ends)) if i not in matched_top]

        return matches, unmatched_top, list(unmatched_bottom)


class TestPatternContinuity(unittest.TestCase):
    """
    图案连续性检测算法完整测试（依赖numpy和opencv）

    测试完整功能：
    - 方法A和方法B的对比
    - 可视化功能
    - 自适应阈值
    - 各种实际图像场景
    """

    def setUp(self):
        """测试前设置"""
        try:
            import numpy as np
            import cv2
            self.np = np
            self.cv2 = cv2
            self.has_deps = True
        except ImportError:
            self.has_deps = False

    def test_method_comparison(self):
        """测试方法A和方法B的对比"""
        if not self.has_deps:
            self.skipTest("numpy或opencv未安装")

        # 配置
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

        # 创建测试图像：连续的图案
        image = self._create_test_image_continuous()

        # 导入函数
        from services.analyzers.detect_pattern_continuity import detect_pattern_continuity

        # 方法A
        score_a, details_a = detect_pattern_continuity(image, conf, method='A', visualize=False)
        # 方法B
        score_b, details_b = detect_pattern_continuity(image, conf, method='B', visualize=False)

        # 两种方法的结果应该一致
        self.assertEqual(score_a, score_b)
        self.assertEqual(details_a['is_continuous'], details_b['is_continuous'])

    def test_continuous_pattern(self):
        """测试连续的图案（完美匹配）"""
        if not self.has_deps:
            self.skipTest("numpy或opencv未安装")

        conf = self._get_default_conf()
        image = self._create_test_image_continuous()

        from services.analyzers.detect_pattern_continuity import detect_pattern_continuity
        score, details = detect_pattern_continuity(image, conf, method='A')

        self.assertEqual(score, 10)
        self.assertTrue(details['is_continuous'])
        self.assertEqual(len(details['unmatched_bottom']), 0)

    def test_discontinuous_pattern(self):
        """测试不连续的图案（线条错位）"""
        if not self.has_deps:
            self.skipTest("numpy或opencv未安装")

        conf = self._get_default_conf()
        image = self._create_test_image_discontinuous()

        from services.analyzers.detect_pattern_continuity import detect_pattern_continuity
        score, details = detect_pattern_continuity(image, conf, method='A')

        self.assertEqual(score, 0)
        self.assertFalse(details['is_continuous'])

    def test_one_to_many_matching(self):
        """测试一对多匹配（粗线覆盖多细线）"""
        if not self.has_deps:
            self.skipTest("numpy或opencv未安装")

        conf = self._get_default_conf()
        image = self._create_test_image_one_to_many()

        from services.analyzers.detect_pattern_continuity import detect_pattern_continuity
        score, details = detect_pattern_continuity(image, conf, method='A')

        self.assertEqual(score, 10)
        self.assertTrue(details['is_continuous'])
        self.assertEqual(len(details['unmatched_bottom']), 0)

    def test_empty_edges(self):
        """测试空边缘"""
        if not self.has_deps:
            self.skipTest("numpy或opencv未安装")

        conf = self._get_default_conf()
        image = self._create_test_image_empty()

        from services.analyzers.detect_pattern_continuity import detect_pattern_continuity
        score, details = detect_pattern_continuity(image, conf, method='A')

        self.assertEqual(score, 10)
        self.assertTrue(details['is_continuous'])

    def test_visualization(self):
        """测试可视化功能"""
        if not self.has_deps:
            self.skipTest("numpy或opencv未安装")

        conf = self._get_default_conf()
        image = self._create_test_image_continuous()

        from services.analyzers.detect_pattern_continuity import detect_pattern_continuity
        score, details = detect_pattern_continuity(image, conf, method='A', visualize=True)

        # 检查可视化图像是否生成
        self.assertIsNotNone(details['visualization'])
        self.assertEqual(details['visualization'].shape[2], 3)  # RGB图像

    # ============ 辅助方法 ============

    def _get_default_conf(self):
        """获取默认配置"""
        return {
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

    def _create_test_image_continuous(self):
        """创建测试图像：连续的图案"""
        image = self.np.ones((128, 128), dtype=self.np.uint8) * 255

        # 绘制顶部细线
        self.cv2.line(image, (20, 0), (20, 3), 0, 1)
        self.cv2.line(image, (50, 0), (50, 3), 0, 1)
        self.cv2.line(image, (80, 0), (80, 3), 0, 1)

        # 绘制底部细线
        self.cv2.line(image, (20, 124), (20, 127), 0, 1)
        self.cv2.line(image, (50, 124), (50, 127), 0, 1)
        self.cv2.line(image, (80, 124), (80, 127), 0, 1)

        return image

    def _create_test_image_discontinuous(self):
        """创建测试图像：不连续的图案"""
        image = self.np.ones((128, 128), dtype=self.np.uint8) * 255

        # 绘制顶部细线
        self.cv2.line(image, (20, 0), (20, 3), 0, 1)
        self.cv2.line(image, (50, 0), (50, 3), 0, 1)
        self.cv2.line(image, (80, 0), (80, 3), 0, 1)

        # 绘制底部细线（错位）
        self.cv2.line(image, (25, 124), (25, 127), 0, 1)
        self.cv2.line(image, (55, 124), (55, 127), 0, 1)
        self.cv2.line(image, (85, 124), (85, 127), 0, 1)

        return image

    def _create_test_image_one_to_many(self):
        """创建测试图像：粗线覆盖多细线"""
        image = self.np.ones((128, 128), dtype=self.np.uint8) * 255

        # 绘制顶部粗线
        self.cv2.rectangle(image, (10, 0), (60, 3), 0, -1)

        # 绘制底部细线
        self.cv2.line(image, (15, 124), (15, 127), 0, 1)
        self.cv2.line(image, (25, 124), (25, 127), 0, 1)
        self.cv2.line(image, (55, 124), (55, 127), 0, 1)

        return image

    def _create_test_image_empty(self):
        """创建测试图像：空边缘"""
        image = self.np.ones((128, 128), dtype=self.np.uint8) * 255
        return image


if __name__ == '__main__':
    unittest.main()
