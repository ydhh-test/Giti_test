# -*- coding: utf-8 -*-
"""
图案连续性检测算法单元测试（新架构 dev2）

测试目标：src.core.detection.pattern_continuity
API 注意：detect_pattern_continuity() 使用显式参数，返回显式 tuple。
PatternContinuityConfig 仅作为算法内部配置数据类，不作为函数入参。

主要变更（相对 dev 分支）：
- import 路径：algorithms.detection.* → src.core.detection.*
- 输入输出：dict 进出 → 显式参数和显式 tuple 返回

最重要的测试验证逻辑：
- 使用真实连续轮胎小图验证算法主判断：center_inf 与 side_inf 正例都应返回 is_continuous=True。
- 使用合成图验证基础层 API 边界：只返回 (is_continuous, vis_name, vis_image)，不返回 score 或端点细节。
- 使用 is_debug=True 验证算法只产出 debug 图像和建议名称，不在算法层保存文件。
"""

import sys
import pathlib
import unittest
from itertools import product

_ROOT = pathlib.Path(__file__).parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ============================================================
# 匹配逻辑白盒测试（不依赖 numpy/opencv）
# ============================================================

class TestMatchEndsLogic(unittest.TestCase):
    """
    复现 _match_ends 核心匹配逻辑，以白盒方式验证
    细线-细线、粗线-细线、粗线-粗线等匹配场景。

    不依赖 numpy/opencv；逻辑自包含。
    """

    def _can_match(self, top_end, bottom_end, fine_match_distance=4):
        top_min, top_max, top_type = top_end
        bot_min, bot_max, bot_type = bottom_end
        if top_type == 'fine' and bot_type == 'fine':
            return abs(top_min - bot_min) <= fine_match_distance
        if top_type == 'fine' and bot_type == 'coarse':
            return bot_min <= top_min <= bot_max
        if top_type == 'coarse' and bot_type == 'fine':
            return top_min <= bot_min <= top_max
        # coarse-coarse
        overlap = min(top_max, bot_max) - max(top_min, bot_min) + 1
        return overlap > 0

    def _match_ends(self, top_ends, bottom_ends, fine_match_distance=4):
        unmatched_bottom = set(range(len(bottom_ends)))
        matches = []
        for ti, bi in product(range(len(top_ends)), range(len(bottom_ends))):
            if bi in unmatched_bottom:
                if self._can_match(top_ends[ti], bottom_ends[bi],
                                   fine_match_distance):
                    unmatched_bottom.remove(bi)
                    matches.append((ti, bi))
        matched_top = {ti for ti, _ in matches}
        unmatched_top = [i for i in range(len(top_ends)) if i not in matched_top]
        return matches, unmatched_top, list(unmatched_bottom)

    # ── 场景测试 ──────────────────────────────────────────────────

    def test_perfect_match(self):
        """完美匹配：所有端点对齐 → is_continuous==True"""
        top = [(20, 20, 'fine'), (50, 50, 'fine'), (80, 80, 'fine')]
        bot = [(20, 20, 'fine'), (50, 50, 'fine'), (80, 80, 'fine')]
        matches, _, unmatched_bot = self._match_ends(top, bot)
        self.assertEqual(len(matches), 3)
        self.assertFalse(unmatched_bot)  # is_continuous

    def test_large_offset_fails(self):
        """错位超过 fine_match_distance → 不连续"""
        top = [(20, 20, 'fine'), (50, 50, 'fine')]
        bot = [(25, 25, 'fine'), (55, 55, 'fine')]
        _, _, unmatched_bot = self._match_ends(top, bot)
        self.assertEqual(len(unmatched_bot), 2)

    def test_coarse_covers_fine(self):
        """粗线覆盖多细线（一对多匹配）"""
        top = [(10, 60, 'coarse')]
        bot = [(15, 15, 'fine'), (25, 25, 'fine'), (55, 55, 'fine')]
        matches, _, unmatched_bot = self._match_ends(top, bot)
        self.assertFalse(unmatched_bot)  # all matched

    def test_empty_edges(self):
        """空边缘 → 连续（无未匹配的底边缘）"""
        _, _, unmatched_bot = self._match_ends([], [])
        self.assertFalse(unmatched_bot)

    def test_top_empty_bot_nonempty(self):
        """顶部空 → 底部全部未匹配 → 不连续"""
        bot = [(20, 20, 'fine'), (50, 50, 'fine')]
        _, _, unmatched_bot = self._match_ends([], bot)
        self.assertEqual(len(unmatched_bot), 2)

    def test_count_mismatch_still_continuous(self):
        """顶部多于底部，底部全匹配 → 连续"""
        top = [(20, 20, 'fine'), (50, 50, 'fine'), (80, 80, 'fine')]
        bot = [(20, 20, 'fine'), (50, 50, 'fine')]
        _, _, unmatched_bot = self._match_ends(top, bot)
        self.assertFalse(unmatched_bot)


# ============================================================
# 完整测试（依赖 numpy / opencv）
# ============================================================

try:
    import numpy as np
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


def _gray_image(h=128, w=128, value=200):
    return np.full((h, w), value, dtype=np.uint8)


@unittest.skipUnless(_HAS_CV2, "需要 numpy 和 opencv-python")
class TestPatternContinuityFull(unittest.TestCase):
    """
    使用合成灰度图验证 detect_pattern_continuity 完整流程。

    API：返回 (is_continuous, vis_name, vis_image)，不再在 core 层计算 score。
    """

    def _run(self, img, **kwargs):
        from src.core.detection.pattern_continuity import detect_pattern_continuity
        return detect_pattern_continuity(img, **kwargs)

    # ── 输入验证 ────────────────────────────────────────────────────

    def test_none_image_returns_err(self):
        """传入 None 应抛出 InputDataError"""
        from src.common.exceptions import InputDataError
        with self.assertRaises(InputDataError):
            self._run(None)

    def test_wrong_ndim_returns_err(self):
        """传入 3D BGR 图像应抛出 InputDataError"""
        from src.common.exceptions import InputDataError
        img3d = np.zeros((128, 128, 3), dtype=np.uint8)
        with self.assertRaises(InputDataError):
            self._run(img3d)

    # ── 输出结构 ────────────────────────────────────────────────────

    def test_output_fields(self):
        """输出显式 tuple 包含所有必需字段"""
        img = _gray_image()
        result = self._run(img)
        self.assertEqual(len(result), 3)
        is_continuous, vis_name, vis_image = result
        self.assertIsInstance(is_continuous, bool)
        self.assertEqual(vis_name, "")
        self.assertIsNone(vis_image)

    def test_output_has_no_score(self):
        """core 层只输出特征，不输出评分字段"""
        img = _gray_image()
        result = self._run(img)
        self.assertEqual(len(result), 3)

    def test_is_continuous_is_bool(self):
        """is_continuous 应为 bool"""
        img = _gray_image()
        is_continuous, _, _ = self._run(img)
        self.assertIsInstance(is_continuous, bool)

    def test_debug_returns_visualization_without_saving(self):
        """is_debug=True 时返回建议文件名和可视化图像，不在算法层保存文件"""
        img = _gray_image()
        _, vis_name, vis_image = self._run(img, is_debug=True)
        self.assertEqual(vis_name, "pattern_continuity.png")
        self.assertIsNotNone(vis_image)
        self.assertEqual(vis_image.shape[:2], img.shape)

    def test_explicit_parameter_override(self):
        """显式参数应可覆盖默认检测参数"""
        img = _gray_image()
        is_continuous, _, _ = self._run(img, threshold=180, edge_height=8)
        self.assertIsInstance(is_continuous, bool)

    # ── 全白图（无线条）────────────────────────────────────────────

    def test_all_white_image_no_crash(self):
        """全白图（无深色线条）：不崩溃，输出结构完整"""
        img = _gray_image(value=255)
        is_continuous, _, _ = self._run(img)
        self.assertIsInstance(is_continuous, bool)

    def test_all_black_image_no_crash(self):
        """全黑图：不崩溃，输出结构完整"""
        img = _gray_image(value=0)
        is_continuous, _, _ = self._run(img)
        self.assertIsInstance(is_continuous, bool)


# ============================================================
# 真实图片测试（依赖 tests/datasets 数据集）
# ============================================================

_DATASET_PC = (
    _ROOT / "tests/datasets"
    / "test_pattern_continuity"
)
_HAS_DATASET_PC = (_DATASET_PC / "center_inf").exists()


@unittest.skipUnless(_HAS_CV2 and _HAS_DATASET_PC,
                     "需要 opencv 和 tests/datasets/test_pattern_continuity 数据集")
class TestPatternContinuityRealImages(unittest.TestCase):
    """
    使用真实轮胎小图验证 detect_pattern_continuity 的健壮性。

    数据集均来自 test_pattern_continuity 目录，图片均为灰度小图。
    """

    def _run(self, path: pathlib.Path):
        from src.core.detection.pattern_continuity import (
            detect_pattern_continuity,
        )
        buf = np.fromfile(str(path), dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)
        self.assertIsNotNone(img, f"无法读取图片: {path}")
        return detect_pattern_continuity(img)

    def _iter_images(self, subdir: str):
        return sorted((_DATASET_PC / subdir).glob("*.png"))

    # ── center_inf ────────────────────────────────────────────────

    def test_center_inf_no_crash(self):
        """center_inf 所有图片均可正常处理，不抛出异常"""
        for p in self._iter_images("center_inf"):
            with self.subTest(img=p.name):
                result = self._run(p)
                is_continuous, _, _ = result
                self.assertIsInstance(is_continuous, bool)

    def test_center_inf_no_score_key(self):
        """center_inf → core 层真实图片输出不包含 score 字段"""
        for p in self._iter_images("center_inf"):
            with self.subTest(img=p.name):
                result = self._run(p)
                self.assertEqual(len(result), 3)

    def test_side_inf_no_score_key(self):
        """side_inf → core 层真实图片输出不包含 score 字段"""
        for p in self._iter_images("side_inf"):
            with self.subTest(img=p.name):
                result = self._run(p)
                self.assertEqual(len(result), 3)

    def test_center_inf_is_continuous_is_bool(self):
        """center_inf → is_continuous 为 bool"""
        for p in self._iter_images("center_inf"):
            with self.subTest(img=p.name):
                result = self._run(p)
                is_continuous, _, _ = result
                self.assertIsInstance(is_continuous, bool)

    def test_center_inf_continuous_images_pass(self):
        """center_inf 真实连续图片应被判定为 is_continuous=True"""
        for p in self._iter_images("center_inf"):
            with self.subTest(img=p.name):
                result = self._run(p)
                is_continuous, _, _ = result
                self.assertTrue(
                    is_continuous,
                    f"{p.name} 应为连续图案（is_continuous=False）"
                )

    # ── side_inf ──────────────────────────────────────────────────

    def test_side_inf_no_crash(self):
        """side_inf 所有图片均可正常处理"""
        for p in self._iter_images("side_inf"):
            with self.subTest(img=p.name):
                result = self._run(p)
                is_continuous, _, _ = result
                self.assertIsInstance(is_continuous, bool)

    def test_side_inf_continuous_images_pass(self):
        """side_inf 真实连续图片应被判定为 is_continuous=True"""
        for p in self._iter_images("side_inf"):
            with self.subTest(img=p.name):
                result = self._run(p)
                is_continuous, _, _ = result
                self.assertTrue(
                    is_continuous,
                    f"{p.name} 应为连续图案（is_continuous=False）"
                )


if __name__ == "__main__":
    unittest.main()
