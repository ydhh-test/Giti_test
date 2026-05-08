# -*- coding: utf-8 -*-
"""
横沟检测算法单元测试（新架构 dev2）

测试目标：src.core.detection.groove_intersection
评分测试独立到 tests/unittests/rules/scores/test_rule_8.py
                tests/unittests/rules/scores/test_rule_14.py

主要变更（相对 dev 分支）：
- import 路径：algorithms.detection.* → src.core.detection.*
- API 变更：detect_transverse_grooves() 返回 dict（不再是 (score, details) 元组）
- details 中不含 score_req8 / score_req14（评分已迁移至 rules/scores 层）
"""

import sys
import pathlib
import unittest

_ROOT = pathlib.Path(__file__).parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ============================================================
# 简化测试：评分边界（不依赖 numpy/opencv）
# 改为直接使用 src.rules.scores 层的函数
# ============================================================

class TestScoresViaRulesLayer(unittest.TestCase):
    """
    验证 Rule 8 / Rule 14 评分逻辑（通过 rules/scores 层，白盒测试）。

    不依赖 numpy/opencv，不依赖图像数据。
    """

    def setUp(self):
        from src.rules.scores.rule_8 import score as score_8
        from src.rules.scores.rule_14 import score as score_14
        self._score_8  = score_8
        self._score_14 = score_14
        self._MAX_REQ8  = 4
        self._MAX_REQ14 = 2

    # ── Rule 8: RIB1/5 ─────────────────────────────────────────────

    def test_req8_rib15_count1_pass(self):
        """RIB1/5 grooves==1 → req8 满分"""
        self.assertEqual(self._score_8(1, "RIB1/5"), self._MAX_REQ8)

    def test_req8_rib15_count0_fail(self):
        """RIB1/5 grooves==0 → req8 零分"""
        self.assertEqual(self._score_8(0, "RIB1/5"), 0)

    def test_req8_rib15_count2_fail(self):
        """RIB1/5 grooves==2 → req8 零分（超过1个）"""
        self.assertEqual(self._score_8(2, "RIB1/5"), 0)

    # ── Rule 8: RIB2/3/4 ───────────────────────────────────────────

    def test_req8_rib234_count0_pass(self):
        """RIB2/3/4 grooves==0 → req8 满分（≤1）"""
        self.assertEqual(self._score_8(0, "RIB2/3/4"), self._MAX_REQ8)

    def test_req8_rib234_count1_pass(self):
        """RIB2/3/4 grooves==1 → req8 满分（≤1）"""
        self.assertEqual(self._score_8(1, "RIB2/3/4"), self._MAX_REQ8)

    def test_req8_rib234_count2_fail(self):
        """RIB2/3/4 grooves==2 → req8 零分（>1）"""
        self.assertEqual(self._score_8(2, "RIB2/3/4"), 0)

    # ── Rule 14: 交叉点数量 ─────────────────────────────────────────

    def test_req14_at_limit_pass(self):
        """交叉点==max_intersections → req14 满分"""
        self.assertEqual(self._score_14(2, max_intersections=2), self._MAX_REQ14)

    def test_req14_below_limit_pass(self):
        """交叉点<max_intersections → req14 满分"""
        self.assertEqual(self._score_14(0, max_intersections=2), self._MAX_REQ14)

    def test_req14_over_limit_fail(self):
        """交叉点>max_intersections → req14 零分"""
        self.assertEqual(self._score_14(3, max_intersections=2), 0)

    # ── 组合 ──────────────────────────────────────────────────────

    def test_combined_perfect(self):
        """全满足 → 6 分"""
        self.assertEqual(self._score_8(1, "RIB1/5") + self._score_14(1), 6)

    def test_combined_zero(self):
        """全不满足 → 0 分"""
        self.assertEqual(self._score_8(0, "RIB1/5") + self._score_14(5), 0)


# ============================================================
# 完整测试（依赖 numpy / opencv）
# ============================================================

try:
    import numpy as np
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


def _make_white_image(h=128, w=128):
    return np.full((h, w, 3), 220, dtype=np.uint8)


def _make_groove_mask(h=128, w=128, band_rows=None):
    mask = np.zeros((h, w), dtype=np.uint8)
    if band_rows:
        for y_start, y_end in band_rows:
            mask[y_start:y_end, :] = 255
    return mask


def _draw_hband(img, y_start, y_end, value=25):
    img[y_start:y_end, :] = value
    return img


def _draw_vband(img, x_start, x_end, value=25):
    img[:, x_start:x_end] = value
    return img


@unittest.skipUnless(_HAS_CV2, "需要 numpy 和 opencv-python")
class TestTransverseGroovesFull(unittest.TestCase):
    """
    使用合成 128×128 BGR 图像验证 detect_transverse_grooves 完整流程。

    API 变更：返回值为 dict（不再是 (score, details) 元组）。
    """

    PIXEL_PER_MM = 7.1

    def _run(self, img, image_type, max_intersections=2):
        from src.core.detection.groove_intersection import detect_transverse_grooves
        return detect_transverse_grooves(
            img, image_type,
            pixel_per_mm=self.PIXEL_PER_MM,
            max_intersections=max_intersections,
        )

    # ── 输入验证 ────────────────────────────────────────────────────

    def test_none_image_returns_err(self):
        """传入 None 应返回含 err_msg 的 dict"""
        d = self._run(None, "center")
        self.assertIn("err_msg", d)

    def test_wrong_ndim_returns_err(self):
        """传入 2D 灰度图应返回含 err_msg 的 dict"""
        gray = np.zeros((128, 128), dtype=np.uint8)
        d = self._run(gray, "center")
        self.assertIn("err_msg", d)

    def test_invalid_image_type_returns_err(self):
        """传入未知 image_type 应返回含 err_msg 的 dict"""
        d = self._run(_make_white_image(), "unknown_type")
        self.assertIn("err_msg", d)

    # ── 输出结构 ────────────────────────────────────────────────────

    def test_output_structure_center(self):
        """center 输入：dict 包含所有必需键，无 score_req8/score_req14"""
        d = self._run(_make_white_image(), "center")
        required = {"rib_type", "groove_count", "intersection_count",
                    "is_valid", "groove_mask", "groove_positions", "debug_image"}
        self.assertTrue(required.issubset(d.keys()))
        # 不应包含评分字段（已迁移到 rules/scores 层）
        self.assertNotIn("score_req8",  d)
        self.assertNotIn("score_req14", d)
        self.assertEqual(d["rib_type"], "RIB1/5")

    def test_output_structure_side(self):
        """side 输入：rib_type 为 RIB2/3/4"""
        d = self._run(_make_white_image(), "side")
        self.assertEqual(d["rib_type"], "RIB2/3/4")

    def test_groove_mask_shape(self):
        """groove_mask 尺寸与输入图像一致"""
        d = self._run(_make_white_image(), "center")
        self.assertEqual(d["groove_mask"].shape, (128, 128))

    def test_debug_image_shape(self):
        """debug_image 尺寸与输入图像一致且为三通道"""
        d = self._run(_make_white_image(), "side")
        self.assertEqual(d["debug_image"].shape, (128, 128, 3))

    # ── 全白图（无横沟）────────────────────────────────────────────

    def test_no_groove_white_image_center(self):
        """全白图 center：groove_count==0，不崩溃"""
        d = self._run(_make_white_image(), "center")
        self.assertEqual(d["groove_count"], 0)

    def test_no_groove_white_image_side(self):
        """全白图 side：groove_count==0，不崩溃"""
        d = self._run(_make_white_image(), "side")
        self.assertEqual(d["groove_count"], 0)

    # ── _analyze_grooves 单元测试（直接构造掩码）───────────────────

    def test_analyze_grooves_single_band_center(self):
        """1条全宽横沟 → count==1"""
        from src.core.detection.groove_intersection import _analyze_grooves
        mask = _make_groove_mask(band_rows=[(50, 80)])
        positions, count, _ = _analyze_grooves(mask, groove_px=25, img_w=128)
        self.assertEqual(count, 1)
        self.assertEqual(len(positions), 1)
        self.assertGreaterEqual(positions[0], 50)
        self.assertLessEqual(positions[0], 80)

    def test_analyze_grooves_two_bands(self):
        """2条横沟 → count==2"""
        from src.core.detection.groove_intersection import _analyze_grooves
        mask = _make_groove_mask(band_rows=[(20, 46), (82, 108)])
        _, count, _ = _analyze_grooves(mask, groove_px=25, img_w=128)
        self.assertEqual(count, 2)

    def test_analyze_grooves_too_narrow_filtered(self):
        """宽度不足的细带应被过滤 → count==0"""
        from src.core.detection.groove_intersection import _analyze_grooves
        mask = _make_groove_mask(band_rows=[(60, 63)])
        _, count, _ = _analyze_grooves(mask, groove_px=25, img_w=128)
        self.assertEqual(count, 0)

    def test_analyze_grooves_positions_sorted(self):
        """多横沟 groove_positions 应升序"""
        from src.core.detection.groove_intersection import _analyze_grooves
        mask = _make_groove_mask(band_rows=[(80, 106), (20, 46)])
        positions, _, _ = _analyze_grooves(mask, groove_px=25, img_w=128)
        self.assertEqual(positions, sorted(positions))

    # ── 交叉点（intersection_count）────────────────────────────────

    def test_intersection_count_nonnegative(self):
        """交叉点数量应为非负整数"""
        img = _make_white_image()
        _draw_hband(img, 50, 80)
        _draw_vband(img, 30, 33)
        d = self._run(img, "center")
        self.assertIsInstance(d["intersection_count"], int)
        self.assertGreaterEqual(d["intersection_count"], 0)

    # ── 大小写不敏感 ─────────────────────────────────────────────

    def test_image_type_case_insensitive(self):
        """CENTER / Center / center 应被同等处理"""
        img = _make_white_image()
        for t in ["CENTER", "Center", "center"]:
            d = self._run(img, t)
            self.assertNotIn("err_msg", d)


# ============================================================
# 真实图片测试（依赖 tests/datasets 数据集）
# ============================================================

_DATASET_9F8D = _ROOT / "tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed"
_HAS_DATASET_9F8D = (_DATASET_9F8D / "center_inf").exists()


@unittest.skipUnless(_HAS_CV2 and _HAS_DATASET_9F8D,
                     "需要 opencv 和 tests/datasets/task_id_9f8d7b6a... 数据集")
class TestTransverseGroovesRealImages(unittest.TestCase):
    """
    使用真实轮胎小图验证 detect_transverse_grooves 的健壮性。

    不断言具体检测数值（无人工标注），仅验证：
    - 函数正常返回，无异常崩溃
    - 输出 dict 包含全部必需键
    - 数值类型和范围合理
    """

    REQUIRED_KEYS = frozenset({
        "rib_type", "groove_count", "intersection_count",
        "is_valid", "groove_mask", "groove_positions", "debug_image",
    })

    def _run(self, path: pathlib.Path, image_type: str):
        from src.core.detection.groove_intersection import detect_transverse_grooves
        buf = np.fromfile(str(path), dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        self.assertIsNotNone(img, f"无法读取图片: {path}")
        return detect_transverse_grooves(img, image_type)

    def _iter_images(self, subdir: str):
        return sorted((_DATASET_9F8D / subdir).glob("*.png"))

    # ── center_inf（RIB1/5）──────────────────────────────────────

    def test_center_inf_no_error(self):
        """center_inf 所有图片均可正常处理（无 err_msg）"""
        for p in self._iter_images("center_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "center")
                self.assertNotIn("err_msg", d, f"处理失败: {p.name}")

    def test_center_inf_required_keys(self):
        """center_inf 输出 dict 包含全部必需键"""
        for p in self._iter_images("center_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "center")
                if "err_msg" in d:
                    continue
                self.assertTrue(self.REQUIRED_KEYS.issubset(d.keys()))

    def test_center_inf_rib_type(self):
        """center_inf → rib_type == RIB1/5"""
        for p in self._iter_images("center_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "center")
                if "err_msg" in d:
                    continue
                self.assertEqual(d["rib_type"], "RIB1/5")

    def test_center_inf_groove_count_nonnegative(self):
        """center_inf → groove_count 非负整数"""
        for p in self._iter_images("center_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "center")
                if "err_msg" in d:
                    continue
                self.assertGreaterEqual(d["groove_count"], 0)

    # ── side_inf（RIB2/3/4）──────────────────────────────────────

    def test_side_inf_no_error(self):
        """side_inf 所有图片均可正常处理"""
        for p in self._iter_images("side_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "side")
                self.assertNotIn("err_msg", d, f"处理失败: {p.name}")

    def test_side_inf_rib_type(self):
        """side_inf → rib_type == RIB2/3/4"""
        for p in self._iter_images("side_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "side")
                if "err_msg" in d:
                    continue
                self.assertEqual(d["rib_type"], "RIB2/3/4")

    # ── 输出格式 ──────────────────────────────────────────────────

    def test_groove_mask_binary(self):
        """groove_mask 仅含 0/255"""
        for p in self._iter_images("center_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "center")
                if "err_msg" in d:
                    continue
                unique = set(np.unique(d["groove_mask"]).tolist())
                self.assertTrue(unique.issubset({0, 255}))

    def test_positions_count_consistent(self):
        """groove_positions 长度等于 groove_count"""
        for p in self._iter_images("center_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "center")
                if "err_msg" in d:
                    continue
                self.assertEqual(len(d["groove_positions"]), d["groove_count"])


if __name__ == "__main__":
    unittest.main()
