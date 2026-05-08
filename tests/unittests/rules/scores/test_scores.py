# -*- coding: utf-8 -*-
"""
规则评分层单元测试（新架构 dev2）

测试目标：
- src.rules.scores.rule_8   (Rule 8：横沟数量约束)
- src.rules.scores.rule_14  (Rule 14：交叉点数量约束)
- src.rules.scores.rule_11  (Rule 11：纵向线条数量约束)
- src.rules.scores.rule_13  (Rule 13：海陆比三级评分)
- src.rules.scores.rule_6_1 (Rule 6_1：节距连续性)

评分函数均为纯函数（只接受特征值，不依赖图像或 configs）。
"""

import sys
import pathlib
import unittest

_ROOT = pathlib.Path(__file__).parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ============================================================
# Rule 8：横沟数量（满分 4）
# ============================================================

class TestRule8Score(unittest.TestCase):

    def setUp(self):
        from src.rules.scores.rule_8 import score
        self._score = score

    def test_rib15_exactly_one_pass(self):
        self.assertEqual(self._score(1, "RIB1/5"), 4)

    def test_rib15_zero_fail(self):
        self.assertEqual(self._score(0, "RIB1/5"), 0)

    def test_rib15_two_fail(self):
        self.assertEqual(self._score(2, "RIB1/5"), 0)

    def test_rib234_zero_pass(self):
        self.assertEqual(self._score(0, "RIB2/3/4"), 4)

    def test_rib234_one_pass(self):
        self.assertEqual(self._score(1, "RIB2/3/4"), 4)

    def test_rib234_two_fail(self):
        self.assertEqual(self._score(2, "RIB2/3/4"), 0)

    def test_custom_max_score(self):
        self.assertEqual(self._score(1, "RIB1/5", max_score=8), 8)


# ============================================================
# Rule 14：交叉点数量（满分 2）
# ============================================================

class TestRule14Score(unittest.TestCase):

    def setUp(self):
        from src.rules.scores.rule_14 import score
        self._score = score

    def test_zero_intersections_pass(self):
        self.assertEqual(self._score(0), 2)

    def test_at_limit_pass(self):
        self.assertEqual(self._score(2, max_intersections=2), 2)

    def test_over_limit_fail(self):
        self.assertEqual(self._score(3, max_intersections=2), 0)

    def test_tight_limit_zero_pass(self):
        self.assertEqual(self._score(0, max_intersections=0), 2)

    def test_tight_limit_one_fail(self):
        self.assertEqual(self._score(1, max_intersections=0), 0)

    def test_custom_max_score(self):
        self.assertEqual(self._score(0, max_score=5), 5)


# ============================================================
# Rule 11：纵向线条数量（满分 4）
# ============================================================

class TestRule11Score(unittest.TestCase):

    def setUp(self):
        from src.rules.scores.rule_11 import score
        self._score = score

    def test_center_at_limit_pass(self):
        """center: count==2 ≤ max_count_center(2) → 满分"""
        self.assertEqual(self._score(2, "center"), 4)

    def test_center_over_limit_fail(self):
        """center: count==3 > 2 → 零分"""
        self.assertEqual(self._score(3, "center"), 0)

    def test_side_at_limit_pass(self):
        """side: count==1 ≤ max_count_side(1) → 满分"""
        self.assertEqual(self._score(1, "side"), 4)

    def test_side_over_limit_fail(self):
        """side: count==2 > 1 → 零分"""
        self.assertEqual(self._score(2, "side"), 0)

    def test_zero_always_pass(self):
        """count==0 对任意类型均满分"""
        for t in ["center", "side"]:
            with self.subTest(image_type=t):
                self.assertEqual(self._score(0, t), 4)

    def test_custom_limits(self):
        """自定义上限参数"""
        from src.rules.scores.rule_11 import score
        self.assertEqual(score(3, "center", max_count_center=3), 4)
        self.assertEqual(score(4, "center", max_count_center=3), 0)


# ============================================================
# Rule 6_1：节距连续性（满分 10）
# ============================================================

class TestRule6_1Score(unittest.TestCase):

    def setUp(self):
        from src.rules.scores.rule_6_1 import score
        self._score = score

    def test_continuous_pass(self):
        """连续 → 满分"""
        self.assertEqual(self._score(True), 10)

    def test_discontinuous_fail(self):
        """不连续 → 零分"""
        self.assertEqual(self._score(False), 0)

    def test_custom_max_score(self):
        """自定义满分"""
        from src.rules.scores.rule_6_1 import score
        self.assertEqual(score(True, max_score=5), 5)
        self.assertEqual(score(False, max_score=5), 0)


if __name__ == "__main__":
    unittest.main()
