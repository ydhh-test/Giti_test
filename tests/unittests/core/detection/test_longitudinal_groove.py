# -*- coding: utf-8 -*-
"""
纵向细沟 & 纵向钢片检测算法单元测试（新架构 dev2）

测试目标：src.core.detection.longitudinal_groove
评分测试独立到 tests/unittests/rules/scores/test_rule_11.py

主要变更（相对 dev 分支）：
- import 路径：algorithms.detection.* → src.core.detection.*
- API 变更：detect_longitudinal_grooves() 返回 dict（不再是 (score, details) 元组）
- details 中不含 "score" 字段（评分已迁移至 rules/scores 层）
- is_valid 保留（结构性约束：count <= max_count）
"""

import sys
import pathlib
import unittest

_ROOT = pathlib.Path(__file__).parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ============================================================
# 简化测试：评分边界（不依赖 numpy/opencv）
# 直接使用 src.rules.scores.rule_11
# ============================================================

class TestScoresViaRulesLayer(unittest.TestCase):
    """验证 Rule 11 评分逻辑（通过 rules/scores 层）"""

    def setUp(self):
        from src.rules.scores.rule_11 import score
        self._score    = score
        self._MAX_SCORE = 4

    # ── RIB1/5 (side)：最多 1 条 ──────────────────────────────────

    def test_side_count0_pass(self):
        """side: 0 条纵线 → 满分（0 ≤ 1）"""
        self.assertEqual(self._score(0, "side"), self._MAX_SCORE)

    def test_side_count1_pass(self):
        """side: 1 条纵线 → 满分（1 ≤ 1）"""
        self.assertEqual(self._score(1, "side"), self._MAX_SCORE)

    def test_side_count2_fail(self):
        """side: 2 条纵线 → 零分（2 > 1）"""
        self.assertEqual(self._score(2, "side"), 0)

    def test_side_count3_fail(self):
        """side: 3 条纵线 → 零分（3 > 1）"""
        self.assertEqual(self._score(3, "side"), 0)

    # ── RIB2/3/4 (center)：最多 2 条 ─────────────────────────────

    def test_center_count0_pass(self):
        """center: 0 条纵线 → 满分（0 ≤ 2）"""
        self.assertEqual(self._score(0, "center"), self._MAX_SCORE)

    def test_center_count2_pass(self):
        """center: 2 条纵线 → 满分（2 ≤ 2）"""
        self.assertEqual(self._score(2, "center"), self._MAX_SCORE)

    def test_center_count3_fail(self):
        """center: 3 条纵线 → 零分（3 > 2）"""
        self.assertEqual(self._score(3, "center"), 0)

    def test_center_count5_fail(self):
        """center: 5 条纵线 → 零分（5 > 2）"""
        self.assertEqual(self._score(5, "center"), 0)


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


def _draw_vband(img, x_start, x_end, value=20):
    img[:, x_start:x_end] = value
    return img


@unittest.skipUnless(_HAS_CV2, "需要 numpy 和 opencv-python")
class TestLongitudinalGroovesFull(unittest.TestCase):
    """
    使用合成 128×128 BGR 图像验证 detect_longitudinal_grooves 完整流程。

    API 变更：返回值为 dict（不再是 (score, details) 元组）。
    """

    PIXEL_PER_MM = 11.81

    def _run(self, img, image_type, **kwargs):
        from src.core.detection.longitudinal_groove import detect_longitudinal_grooves
        return detect_longitudinal_grooves(img, image_type,
                                           pixel_per_mm=self.PIXEL_PER_MM, **kwargs)

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
        d = self._run(_make_white_image(), "top")
        self.assertIn("err_msg", d)

    # ── 输出结构 ────────────────────────────────────────────────────

    def test_output_structure_center(self):
        """center 输入：dict 包含所有必需键，不含 'score' 字段"""
        d = self._run(_make_white_image(), "center")
        required = {"rib_type", "groove_count", "groove_positions",
                    "groove_widths", "is_valid", "line_mask", "debug_image"}
        self.assertTrue(required.issubset(d.keys()))
        self.assertNotIn("score", d)  # 评分已迁移至 rules/scores 层
        self.assertEqual(d["rib_type"], "RIB2/3/4")

    def test_output_structure_side(self):
        """side 输入：rib_type 为 RIB1/5"""
        d = self._run(_make_white_image(), "side")
        self.assertEqual(d["rib_type"], "RIB1/5")

    def test_groove_count_nonnegative(self):
        """groove_count 应为非负整数"""
        d = self._run(_make_white_image(), "center")
        self.assertIsInstance(d["groove_count"], int)
        self.assertGreaterEqual(d["groove_count"], 0)

    def test_positions_is_list(self):
        """groove_positions 应为列表"""
        d = self._run(_make_white_image(), "center")
        self.assertIsInstance(d["groove_positions"], list)

    def test_line_mask_shape(self):
        """line_mask 尺寸与输入图像一致"""
        d = self._run(_make_white_image(), "center")
        self.assertEqual(d["line_mask"].shape, (128, 128))

    def test_debug_image_shape(self):
        """debug_image 为三通道且尺寸一致"""
        d = self._run(_make_white_image(), "side")
        self.assertEqual(d["debug_image"].shape, (128, 128, 3))

    # ── 全白图（无纵线）────────────────────────────────────────────

    def test_no_groove_white_center(self):
        """全白图 center：groove_count==0，is_valid==True（0 ≤ 2）"""
        d = self._run(_make_white_image(), "center")
        self.assertEqual(d["groove_count"], 0)
        self.assertTrue(d["is_valid"])

    def test_no_groove_white_side(self):
        """全白图 side：groove_count==0，is_valid==True（0 ≤ 1）"""
        d = self._run(_make_white_image(), "side")
        self.assertEqual(d["groove_count"], 0)
        self.assertTrue(d["is_valid"])

    # ── is_valid 语义：结构性约束 ─────────────────────────────────

    def test_is_valid_is_bool(self):
        """is_valid 应为 bool 类型"""
        d = self._run(_make_white_image(), "center")
        self.assertIsInstance(d["is_valid"], bool)

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

_DATASET_LG = _ROOT / "tests/datasets/task_longitudinal_groove_vis"
_HAS_DATASET_LG = (_DATASET_LG / "center_inf").exists()


@unittest.skipUnless(_HAS_CV2 and _HAS_DATASET_LG,
                     "需要 opencv 和 tests/datasets/task_longitudinal_groove_vis 数据集")
class TestLongitudinalGrooveRealImages(unittest.TestCase):
    """
    使用真实轮胎小图验证 detect_longitudinal_grooves 的健壮性。

    仅对文件名为纯数字（如 0.png、2.png）的真实图片测试；
    以 syn_ 开头的合成对照图不在此类中验证。
    """

    REQUIRED_KEYS = frozenset({
        "rib_type", "groove_count", "groove_positions",
        "groove_widths", "is_valid", "line_mask", "debug_image",
    })

    def _run(self, path: pathlib.Path, image_type: str):
        from src.core.detection.longitudinal_groove import detect_longitudinal_grooves
        buf = np.fromfile(str(path), dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        self.assertIsNotNone(img, f"无法读取图片: {path}")
        return detect_longitudinal_grooves(img, image_type)

    def _iter_real_images(self, subdir: str):
        """只取文件名为纯数字的真实图片"""
        d = _DATASET_LG / subdir
        return [p for p in sorted(d.glob("*.png")) if p.stem.isdigit()]

    # ── center_inf（RIB2/3/4，最多 2 条）──────────────────────────

    def test_center_inf_no_error(self):
        """center_inf 真实图片均可正常处理（无 err_msg）"""
        for p in self._iter_real_images("center_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "center")
                self.assertNotIn("err_msg", d, f"处理失败: {p.name}")

    def test_center_inf_required_keys(self):
        """center_inf 输出 dict 包含全部必需键"""
        for p in self._iter_real_images("center_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "center")
                if "err_msg" in d:
                    continue
                self.assertTrue(self.REQUIRED_KEYS.issubset(d.keys()))

    def test_center_inf_rib_type(self):
        """center_inf → rib_type == RIB2/3/4"""
        for p in self._iter_real_images("center_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "center")
                if "err_msg" in d:
                    continue
                self.assertEqual(d["rib_type"], "RIB2/3/4")

    def test_center_inf_count_le_max(self):
        """center_inf 真实图片检测到的纵沟数量 ≤ 2（满足 RIB2/3/4 约束）"""
        for p in self._iter_real_images("center_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "center")
                if "err_msg" in d:
                    continue
                self.assertLessEqual(d["groove_count"], 2,
                                     f"{p.name}: groove_count={d['groove_count']} > 2")

    # ── side_inf（RIB1/5，最多 1 条）──────────────────────────────

    def test_side_inf_no_error(self):
        """side_inf 真实图片均可正常处理"""
        for p in self._iter_real_images("side_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "side")
                self.assertNotIn("err_msg", d, f"处理失败: {p.name}")

    def test_side_inf_rib_type(self):
        """side_inf → rib_type == RIB1/5"""
        for p in self._iter_real_images("side_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "side")
                if "err_msg" in d:
                    continue
                self.assertEqual(d["rib_type"], "RIB1/5")

    def test_side_inf_count_le_max(self):
        """side_inf 真实图片检测到的纵沟数量 ≤ 1（满足 RIB1/5 约束）"""
        for p in self._iter_real_images("side_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "side")
                if "err_msg" in d:
                    continue
                self.assertLessEqual(d["groove_count"], 1,
                                     f"{p.name}: groove_count={d['groove_count']} > 1")

    # ── 输出格式 ──────────────────────────────────────────────────

    def test_line_mask_binary(self):
        """line_mask 仅含 0/255"""
        for p in self._iter_real_images("center_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "center")
                if "err_msg" in d:
                    continue
                unique = set(np.unique(d["line_mask"]).tolist())
                self.assertTrue(unique.issubset({0, 255}))

    def test_positions_widths_same_length(self):
        """groove_positions 与 groove_widths 长度应相同"""
        for p in self._iter_real_images("center_inf"):
            with self.subTest(img=p.name):
                d = self._run(p, "center")
                if "err_msg" in d:
                    continue
                self.assertEqual(len(d["groove_positions"]), len(d["groove_widths"]))


if __name__ == "__main__":
    unittest.main()
