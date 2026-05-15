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
- 使用原始轮胎小图验证算法主判断：center_inf 与 side_inf 按逐图预期返回 is_continuous。
- 使用合成图验证基础层 API 边界：只返回 (is_continuous, vis_name, vis_image)，不返回 score 或端点细节。
- 使用 is_debug=True 验证算法只产出 debug 图像和建议名称，不在算法层保存文件。

人工设计的覆盖性测试逻辑：
- 针对公开 API：覆盖正常连续、不连续、输入维度错误、边缘检测失败、匹配失败、debug 可视化失败。
    这些分支对应调用方最关心的成功/失败边界，能验证算法层不会吞掉下层异常。
- 针对边缘提取：覆盖像素扫描方法 A、OpenCV 轮廓方法 B、细线/粗线、噪声过滤和高度不足。
    这些分支决定端点是否被正确识别，是连续性判断的前置基础。
- 针对匹配逻辑：覆盖细线-细线、细线-粗线、粗线-细线、粗线-粗线和未知类型。
    这些组合直接决定 is_continuous 的真假，属于 Rule 6_1 最核心的人工白盒用例。
- 针对debug图：覆盖未匹配端点高亮、细线圆点、粗线矩形、匹配连线和颜色生成。
    debug 图虽不参与评分，但用于人工排查误判，必须保证关键绘制路径可运行。
"""

import pathlib
import unittest
from itertools import product
from unittest import mock

_ROOT = pathlib.Path(__file__).parents[4]


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

    def test_unmatched_bottom_returns_false(self):
        """仅底边缘出现线条时应判定为不连续"""
        img = _gray_image(h=32, w=32, value=255)
        img[-4:, 12] = 0
        is_continuous, vis_name, vis_image = self._run(img)
        self.assertFalse(is_continuous)
        self.assertEqual(vis_name, "")
        self.assertIsNone(vis_image)

    def test_too_short_image_raises_input_error(self):
        """高度不足时应由底层检测抛出 InputDataError"""
        from src.common.exceptions import InputDataError
        img = _gray_image(h=4, w=32, value=255)
        with self.assertRaises(InputDataError):
            self._run(img)

    def test_edge_detection_unexpected_error_is_wrapped(self):
        """边缘检测的未知异常应包装为 RuntimeProcessError"""
        import src.core.detection.pattern_continuity as pc
        from src.common.exceptions import RuntimeProcessError

        img = _gray_image()
        with mock.patch.object(pc, "_detect_with_method_b", side_effect=ValueError("boom")):
            with self.assertRaises(RuntimeProcessError):
                self._run(img)

    def test_match_error_is_wrapped(self):
        """端点匹配异常应包装为 RuntimeProcessError"""
        import src.core.detection.pattern_continuity as pc
        from src.common.exceptions import RuntimeProcessError

        img = _gray_image()
        with mock.patch.object(pc, "_match_ends", side_effect=ValueError("boom")):
            with self.assertRaises(RuntimeProcessError):
                self._run(img)

    def test_debug_visualization_error_is_wrapped(self):
        """debug 可视化异常应包装为 RuntimeProcessError"""
        import src.core.detection.pattern_continuity as pc
        from src.common.exceptions import RuntimeProcessError

        img = _gray_image()
        with mock.patch.object(pc, "_visualize_detection", side_effect=ValueError("boom")):
            with self.assertRaises(RuntimeProcessError):
                self._run(img, is_debug=True)

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


@unittest.skipUnless(_HAS_CV2, "需要 numpy 和 opencv-python")
class TestPatternContinuityInternalBranches(unittest.TestCase):
    """人工设计的白盒分支测试，覆盖核心 if/else。"""

    def test_method_a_extracts_fine_and_coarse_ends(self):
        """方法 A 应同时识别细线点和粗线区间"""
        from src.core.detection.pattern_continuity import (
            PatternContinuityConfig,
            _detect_with_method_a,
        )

        img = _gray_image(h=12, w=12, value=255)
        img[0, 1] = 0
        img[0, 4:7] = 0
        img[-1, 2] = 0
        img[-1, 8:11] = 0
        cfg = PatternContinuityConfig(edge_height=2, coarse_threshold=3)

        top_ends, bottom_ends = _detect_with_method_a(img, cfg)

        self.assertEqual(top_ends, [(1, 1, 'fine'), (4, 6, 'coarse')])
        self.assertEqual(bottom_ends, [(2, 2, 'fine'), (8, 10, 'coarse')])

    def test_method_a_too_short_image_raises_input_error(self):
        """方法 A 高度不足时应走 InputDataError 分支"""
        from src.common.exceptions import InputDataError
        from src.core.detection.pattern_continuity import (
            PatternContinuityConfig,
            _detect_with_method_a,
        )

        img = _gray_image(h=3, w=12, value=255)
        with self.assertRaises(InputDataError):
            _detect_with_method_a(img, PatternContinuityConfig(edge_height=2))

    def test_method_a_unexpected_error_is_wrapped(self):
        """方法 A 内部未知异常应包装为 RuntimeProcessError"""
        import src.core.detection.pattern_continuity as pc
        from src.common.exceptions import RuntimeProcessError

        img = _gray_image(h=12, w=12, value=255)
        with mock.patch.object(pc, "_extract_ends_from_region", side_effect=ValueError("boom")):
            with self.assertRaises(RuntimeProcessError):
                pc._detect_with_method_a(img, pc.PatternContinuityConfig())

    def test_extract_region_filters_short_noise(self):
        """短于 min_line_width 的像素段应被当成噪声过滤"""
        from src.core.detection.pattern_continuity import (
            PatternContinuityConfig,
            _extract_ends_from_region,
        )

        region = np.full((2, 8), 255, dtype=np.uint8)
        region[-1, 3] = 0
        cfg = PatternContinuityConfig(min_line_width=2)

        self.assertEqual(_extract_ends_from_region(region, 200, cfg, is_top=False), [])

    def test_method_b_threshold_error_is_wrapped(self):
        """OpenCV 二值化异常应包装为 RuntimeProcessError"""
        import src.core.detection.pattern_continuity as pc
        from src.common.exceptions import RuntimeProcessError

        img = _gray_image(h=12, w=12, value=255)
        with mock.patch.object(pc.cv2, "threshold", side_effect=ValueError("boom")):
            with self.assertRaises(RuntimeProcessError):
                pc._detect_with_method_b(img, pc.PatternContinuityConfig())

    def test_method_b_unexpected_error_is_wrapped(self):
        """方法 B 轮廓提取未知异常应包装为 RuntimeProcessError"""
        import src.core.detection.pattern_continuity as pc
        from src.common.exceptions import RuntimeProcessError

        img = _gray_image(h=12, w=12, value=255)
        with mock.patch.object(pc, "_extract_ends_from_contours", side_effect=ValueError("boom")):
            with self.assertRaises(RuntimeProcessError):
                pc._detect_with_method_b(img, pc.PatternContinuityConfig())

    def test_extract_contours_fine_coarse_and_noise(self):
        """轮廓提取应覆盖细线、粗线和噪声过滤分支"""
        from src.core.detection.pattern_continuity import (
            PatternContinuityConfig,
            _extract_ends_from_contours,
        )

        fine_region = np.zeros((4, 12), dtype=np.uint8)
        fine_region[:, 2] = 255
        coarse_region = np.zeros((4, 12), dtype=np.uint8)
        coarse_region[:, 5:10] = 255
        noise_region = np.zeros((4, 12), dtype=np.uint8)
        noise_region[:, 1] = 255

        self.assertEqual(
            _extract_ends_from_contours(fine_region, PatternContinuityConfig()),
            [(2, 2, 'fine')]
        )
        self.assertEqual(
            _extract_ends_from_contours(coarse_region, PatternContinuityConfig()),
            [(5, 9, 'coarse')]
        )
        self.assertEqual(
            _extract_ends_from_contours(noise_region, PatternContinuityConfig(min_line_width=2)),
            []
        )

    def test_actual_can_match_all_type_pairs(self):
        """实际匹配函数应覆盖所有线型组合和未知类型兜底"""
        from src.core.detection.pattern_continuity import PatternContinuityConfig, _can_match

        cfg = PatternContinuityConfig(fine_match_distance=4)
        self.assertTrue(_can_match((10, 10, 'fine'), (14, 14, 'fine'), cfg))
        self.assertFalse(_can_match((10, 10, 'fine'), (15, 15, 'fine'), cfg))
        self.assertTrue(_can_match((10, 10, 'fine'), (8, 12, 'coarse'), cfg))
        self.assertTrue(_can_match((8, 12, 'coarse'), (10, 10, 'fine'), cfg))
        self.assertTrue(_can_match((8, 12, 'coarse'), (11, 14, 'coarse'), cfg))
        self.assertFalse(_can_match((8, 10, 'coarse'), (11, 14, 'coarse'), cfg))
        self.assertFalse(_can_match((8, 10, 'unknown'), (8, 10, 'fine'), cfg))

    def test_actual_match_skips_already_matched_bottom(self):
        """多个 top 竞争同一 bottom 时，应只匹配一次并留下未匹配 top"""
        from src.core.detection.pattern_continuity import PatternContinuityConfig, _match_ends

        matches, unmatched_top, unmatched_bottom = _match_ends(
            [(10, 10, 'fine'), (11, 11, 'fine')],
            [(10, 10, 'fine')],
            PatternContinuityConfig(),
        )

        self.assertEqual(matches, [(0, 0)])
        self.assertEqual(unmatched_top, [1])
        self.assertEqual(unmatched_bottom, [])

    def test_visualize_detection_draws_all_key_branches(self):
        """debug 图应覆盖细线/粗线、未匹配高亮和匹配连线绘制"""
        from src.core.detection.pattern_continuity import (
            PatternContinuityConfig,
            _visualize_detection,
        )

        img = _gray_image(h=24, w=24, value=255)
        vis = _visualize_detection(
            image=img,
            top_ends=[(2, 2, 'fine'), (6, 10, 'coarse')],
            bottom_ends=[(3, 3, 'fine'), (7, 11, 'coarse')],
            matches=[(0, 0), (1, 1)],
            unmatched_top=[0],
            unmatched_bottom=[0],
            config=PatternContinuityConfig(edge_height=4),
        )

        self.assertEqual(vis.shape, (24, 24, 3))
        self.assertGreater(int(vis.sum()), int(img.sum()))

    def test_generate_colors_count(self):
        """颜色生成应返回指定数量的 RGB 颜色"""
        from src.core.detection.pattern_continuity import _generate_colors

        colors = _generate_colors(3)
        self.assertEqual(len(colors), 3)
        self.assertTrue(all(len(color) == 3 for color in colors))


# ============================================================
# 真实图片测试（依赖 tests/datasets 数据集）
# ============================================================

_DATASET_PC = (
    _ROOT / "tests/datasets"
    / "test_pattern_continuity"
)
_HAS_DATASET_PC = (_DATASET_PC / "center_inf").exists()
_EXPECTED_REAL_IMAGE_CONTINUITY = {
    "center_inf": {
        "0.png": False,
        "1.png": False,
        "2.png": True,
    },
    "side_inf": {
        "0.png": True,
    },
}
_WISE_IMAGE_DEV1 = _DATASET_PC / "wise_image_dev1"
_WISE_IMAGE_DEV2 = _ROOT / ".results" / "wise_image_dev2" / "test_pattern_continuity"
_HAS_WISE_DEV1 = bool(list(_WISE_IMAGE_DEV1.glob("*.png"))) if _WISE_IMAGE_DEV1.exists() else False


@unittest.skipUnless(_HAS_CV2 and _HAS_DATASET_PC,
                     "需要 opencv 和 tests/datasets/test_pattern_continuity 数据集")
class TestPatternContinuityRealImages(unittest.TestCase):
    """
    使用真实轮胎小图验证 detect_pattern_continuity 的健壮性。

    数据集均来自 feature/dev 的原始 center_inf/side_inf 小图，
    debug 染色图只应由 is_debug=True 的算法输出生成，不能作为输入数据集。
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

    def _load_color(self, path: pathlib.Path):
        buf = np.fromfile(str(path), dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        self.assertIsNotNone(img, f"无法读取图片: {path}")
        return img

    def _assert_no_debug_marker_colors(self, img):
        b, g, r = img[..., 0], img[..., 1], img[..., 2]
        marker_mask = (
            ((g > 220) & (b < 80) & (r < 80))
            | ((r > 220) & (b < 80) & (g < 80))
            | ((b > 220) & (g < 80) & (r < 80))
            | ((r > 220) & (g > 220) & (b < 80))
        )
        self.assertEqual(
            int(marker_mask.sum()),
            0,
            "真实输入图中不应包含 debug 可视化的高饱和标记色",
        )

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

    def test_center_inf_images_match_expected_continuity(self):
        """center_inf 原始图片应按逐图预期返回连续性结果"""
        expected = _EXPECTED_REAL_IMAGE_CONTINUITY["center_inf"]
        for p in self._iter_images("center_inf"):
            with self.subTest(img=p.name):
                result = self._run(p)
                is_continuous, _, _ = result
                self.assertEqual(
                    is_continuous,
                    expected[p.name],
                    f"{p.name} 连续性结果与原图预期不一致"
                )

    def test_real_images_are_raw_inputs_not_debug_visualizations(self):
        """真实输入图不应包含算法 debug 可视化标记色"""
        for subdir in _EXPECTED_REAL_IMAGE_CONTINUITY:
            for p in self._iter_images(subdir):
                with self.subTest(img=f"{subdir}/{p.name}"):
                    self._assert_no_debug_marker_colors(self._load_color(p))

    # ── side_inf ──────────────────────────────────────────────────

    def test_side_inf_no_crash(self):
        """side_inf 所有图片均可正常处理"""
        for p in self._iter_images("side_inf"):
            with self.subTest(img=p.name):
                result = self._run(p)
                is_continuous, _, _ = result
                self.assertIsInstance(is_continuous, bool)

    def test_side_inf_images_match_expected_continuity(self):
        """side_inf 原始图片应按逐图预期返回连续性结果"""
        expected = _EXPECTED_REAL_IMAGE_CONTINUITY["side_inf"]
        for p in self._iter_images("side_inf"):
            with self.subTest(img=p.name):
                result = self._run(p)
                is_continuous, _, _ = result
                self.assertEqual(
                    is_continuous,
                    expected[p.name],
                    f"{p.name} 连续性结果与原图预期不一致"
                )


# ============================================================
# 染色图等价性测试（dev2 vs dev1 老架构）
# ============================================================

@unittest.skipUnless(_HAS_CV2 and _HAS_DATASET_PC,
                     "需要 opencv 和 tests/datasets/test_pattern_continuity 数据集")
class TestPatternContinuityVisualizationEquivalence(unittest.TestCase):
    """
    验证 dev2 新架构的 debug 染色图与 dev1 老架构（feature/dev）完全一致。

    工作流：
    1. test_generate_and_save_dev2_visualizations —— 始终运行，生成 dev2 染色图并写入
       wise_image_dev2/，供人工比对。
    2. test_dev2_visualizations_equal_dev1 —— 仅当 wise_image_dev1/ 中存在老架构染色图时
       才运行，对每张图做 np.array 像素级精确比对，以证明算法等价。

    wise_image_dev1/ 中的图片由开发者在 feature/dev 分支上运行老架构后手动存入，
    命名规则为 {subdir}_{stem}.png（如 center_inf_0.png、side_inf_0.png）。
    """

    # ── 工具方法 ────────────────────────────────────────────────────

    def _load_gray(self, path: pathlib.Path) -> np.ndarray:
        buf = np.fromfile(str(path), dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)
        self.assertIsNotNone(img, f"无法读取灰度图: {path}")
        return img

    def _load_color(self, path: pathlib.Path) -> np.ndarray:
        buf = np.fromfile(str(path), dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        self.assertIsNotNone(img, f"无法读取染色图: {path}")
        return img

    def _save_image(self, path: pathlib.Path, img: np.ndarray) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        success, buf = cv2.imencode(".png", img)
        self.assertTrue(success, f"图片编码失败: {path}")
        path.write_bytes(buf.tobytes())

    @staticmethod
    def _wise_name(subdir: str, stem: str) -> str:
        """统一命名规则：{subdir}_{stem}.png，如 center_inf_0.png"""
        return f"{subdir}_{stem}.png"

    def _iter_real_images(self):
        """遍历所有真实输入图片，yield (subdir, path)"""
        for subdir in _EXPECTED_REAL_IMAGE_CONTINUITY:
            for p in sorted((_DATASET_PC / subdir).glob("*.png")):
                yield subdir, p

    def _run_debug(self, gray_path: pathlib.Path) -> np.ndarray:
        """读取灰度图并运行 detect_pattern_continuity(is_debug=True)，返回染色图"""
        from src.core.detection.pattern_continuity import detect_pattern_continuity
        img = self._load_gray(gray_path)
        _, _, vis_image = detect_pattern_continuity(img, is_debug=True)
        return vis_image

    # ── 测试：生成并保存 dev2 染色图 ───────────────────────────────

    def test_generate_and_save_dev2_visualizations(self):
        """
        对所有真实图片运行新架构（dev2），将染色图保存到 wise_image_dev2/ 供人工比对。
        命名规则：{subdir}_{stem}.png（如 center_inf_0.png）。
        """
        for subdir, p in self._iter_real_images():
            with self.subTest(img=f"{subdir}/{p.name}"):
                vis_image = self._run_debug(p)
                self.assertIsNotNone(vis_image, f"{subdir}/{p.name} 未生成染色图")
                save_path = _WISE_IMAGE_DEV2 / self._wise_name(subdir, p.stem)
                self._save_image(save_path, vis_image)

    # ── 测试：像素级等价性比对 ──────────────────────────────────────

    @unittest.skipUnless(_HAS_WISE_DEV1,
                         "wise_image_dev1/ 为空，跳过等价性比对"
                         "（请先在 feature/dev 分支用老架构生成染色图并存入该目录）")
    def test_dev2_visualizations_equal_dev1(self):
        """
        dev2 新架构生成的染色图与 wise_image_dev1/ 中的 dev1 老架构染色图完全像素等价。

        任意一张图存在差异即视为算法不等价，测试失败。
        若 wise_image_dev1/ 中缺少某张图，该子用例跳过（不算失败）。
        """
        for subdir, p in self._iter_real_images():
            with self.subTest(img=f"{subdir}/{p.name}"):
                wise_name = self._wise_name(subdir, p.stem)
                dev1_path = _WISE_IMAGE_DEV1 / wise_name

                if not dev1_path.exists():
                    self.skipTest(
                        f"wise_image_dev1/{wise_name} 不存在，跳过该图比对"
                    )

                vis_image = self._run_debug(p)
                self.assertIsNotNone(vis_image, f"{subdir}/{p.name} 未生成染色图")

                dev1_img = self._load_color(dev1_path)

                self.assertTrue(
                    np.array_equal(vis_image, dev1_img),
                    f"{subdir}/{p.name} 染色图与 dev1 老架构不完全一致\n"
                    f"  dev2 shape={vis_image.shape}, dev1 shape={dev1_img.shape}\n"
                    f"  最大像素差={int(np.abs(vis_image.astype(int) - dev1_img.astype(int)).max())}"
                )


if __name__ == "__main__":
    unittest.main()
