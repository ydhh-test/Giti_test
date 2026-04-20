# -*- coding: utf-8 -*-

"""
纵向细沟 & 纵向钢片检测算法单元测试（Rule 11）

包含两个测试类：
1. TestLongitudinalGroovesSimple - 不依赖 numpy/opencv，仅测试评分逻辑边界
2. TestLongitudinalGroovesFull   - 依赖 numpy/opencv，用合成 128×128 图像测试完整流程
"""

import sys
import pathlib
import unittest

# 确保项目根目录在 sys.path 中
_ROOT = pathlib.Path(__file__).parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ============================================================
# 简化测试（不依赖 numpy / opencv）
# ============================================================

class TestLongitudinalGroovesSimple(unittest.TestCase):
    """
    不依赖 numpy/opencv 的核心评分逻辑测试。

    直接复现 _compute_score 的判定规则，以白盒方式验证
    RIB1/5（side）和 RIB2/3/4（center）的数量边界条件。

    宽度约束（2026-04 更新）：
    - nominal_px = 0.34mm × 11.81 px/mm ≈ 4.0 px
    - 容差 ±50% → 有效宽度范围 [~2, ~6] px
    """

    _MAX_SCORE = 4  # Rule 11 满分

    # ── 内嵌 _compute_score 逻辑（无外部依赖）──────────────────────
    def _compute_score(self, count: int, max_count: int) -> int:
        """镜像 longitudinal_groove._compute_score 逻辑"""
        return self._MAX_SCORE if count <= max_count else 0

    # ── RIB1/5（side，最多 1 条）────────────────────────────────────

    def test_rib15_count0_pass(self):
        """side: 0 条纵线 → 满分（0 ≤ 1）"""
        self.assertEqual(self._compute_score(0, max_count=1), self._MAX_SCORE)

    def test_rib15_count1_pass(self):
        """side: 1 条纵线 → 满分（1 ≤ 1）"""
        self.assertEqual(self._compute_score(1, max_count=1), self._MAX_SCORE)

    def test_rib15_count2_fail(self):
        """side: 2 条纵线 → 零分（2 > 1）"""
        self.assertEqual(self._compute_score(2, max_count=1), 0)

    def test_rib15_count3_fail(self):
        """side: 3 条纵线 → 零分（3 > 1）"""
        self.assertEqual(self._compute_score(3, max_count=1), 0)

    # ── RIB2/3/4（center，最多 2 条）───────────────────────────────

    def test_rib234_count0_pass(self):
        """center: 0 条纵线 → 满分（0 ≤ 2）"""
        self.assertEqual(self._compute_score(0, max_count=2), self._MAX_SCORE)

    def test_rib234_count1_pass(self):
        """center: 1 条纵线 → 满分（1 ≤ 2）"""
        self.assertEqual(self._compute_score(1, max_count=2), self._MAX_SCORE)

    def test_rib234_count2_pass(self):
        """center: 2 条纵线 → 满分（2 ≤ 2，上限边界）"""
        self.assertEqual(self._compute_score(2, max_count=2), self._MAX_SCORE)

    def test_rib234_count3_fail(self):
        """center: 3 条纵线 → 零分（3 > 2）"""
        self.assertEqual(self._compute_score(3, max_count=2), 0)

    def test_rib234_count4_fail(self):
        """center: 4 条纵线 → 零分（4 > 2）"""
        self.assertEqual(self._compute_score(4, max_count=2), 0)

    # ── 综合评分 ──────────────────────────────────────────────────────

    def test_score_is_max_when_valid(self):
        """合规时得分等于 MAX_SCORE=4"""
        self.assertEqual(self._compute_score(1, max_count=2), 4)

    def test_score_is_zero_when_invalid(self):
        """违规时得分为 0"""
        self.assertEqual(self._compute_score(3, max_count=2), 0)


# ============================================================
# 完整测试（依赖 numpy / opencv）
# ============================================================

try:
    import numpy as np
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


def _make_white_image(h: int = 128, w: int = 128) -> "np.ndarray":
    """生成全亮（灰度 200）的 BGR 图像，无任何线条特征"""
    return np.full((h, w, 3), 200, dtype=np.uint8)


def _make_vline_image(h: int = 128, w: int = 128, vband_cols=None) -> "np.ndarray":
    """
    生成含纵向线条带的合成轮胎纹路图像（适配自适应二值化检测）。

    自适应阈值（blockSize=31, C=5, THRESH_BINARY_INV）依赖局部对比度：
    仅当像素值低于局部均值 - C 时才成为前景。若整个邻域均匀暗淡，
    局部均值也低，阈值随之下移，暗色像素反而不被检测为前景。

    解决方案：在亮色背景（200）上，纵向线条列内按行交替明暗
    （偶数行=20暗，奇数行=190亮），保证 31×31 邻域中始终含亮色像素，
    使局部均值足够高，暗行像素可被正确识别为前景。

    Parameters
    ----------
    h, w       : 图像高度/宽度（像素）
    vband_cols : list of (x_start, x_end)，每条纵线的列范围（左闭右开）
                 默认 None（生成纯白图像）
    """
    img = np.full((h, w, 3), 200, dtype=np.uint8)
    if vband_cols:
        for x_start, x_end in vband_cols:
            for r in range(h):
                val = 20 if (r % 2 == 0) else 190
                img[r, x_start:x_end] = val
    return img


# 宽度参数（与算法默认参数保持一致）
_PIXEL_PER_MM   = 11.81
_GROOVE_WMM     = 0.34
# nominal_px ≈ 4.0，min_w = nominal - 1 = 3px，无上限约束
_NOMINAL_W      = 4  # 合成图像中使用的标称线宽（在容差范围内）


@unittest.skipUnless(_HAS_CV2, "需要 numpy 和 opencv-python")
class TestLongitudinalGroovesFull(unittest.TestCase):
    """
    使用合成 128×128 BGR 图像验证纵向细沟检测的完整流程。

    合成图像约定：
    - 背景：灰度 200（浅色花纹块）
    - 纵向线条：宽 12 px（≈1mm @ 11.81px/mm），各行交替 20/190
    """

    def _run(self, img, image_type):
        from algorithms.detection.longitudinal_groove import detect_longitudinal_grooves
        return detect_longitudinal_grooves(
            img, image_type,
            groove_width_mm=_GROOVE_WMM,
            pixel_per_mm=_PIXEL_PER_MM,
        )

    # ── 输入验证 ────────────────────────────────────────────────────

    def test_none_image_returns_err(self):
        """image=None → 返回 (None, {err_msg, error_type})"""
        score, details = self._run(None, "center")
        self.assertIsNone(score)
        self.assertIn("err_msg", details)

    def test_invalid_dims_returns_err(self):
        """非 3 通道图像 → 返回错误 details"""
        bad = np.zeros((128, 128), dtype=np.uint8)  # 2D grayscale
        score, details = self._run(bad, "center")
        self.assertIsNone(score)
        self.assertIn("err_msg", details)

    def test_unknown_image_type_returns_err(self):
        """未知 image_type → 返回错误 details"""
        img = _make_white_image()
        score, details = self._run(img, "unknown_type")
        self.assertIsNone(score)
        self.assertIn("err_msg", details)

    # ── 纯白图像（无线条）────────────────────────────────────────────

    def test_no_line_white_image_center(self):
        """白图 center → 0 条纵线 → 4 分（0 ≤ 2）"""
        score, details = self._run(_make_white_image(), "center")
        self.assertEqual(score, 4.0)
        self.assertEqual(details["groove_count"], 0)
        self.assertTrue(details["is_valid"])
        self.assertEqual(details["rib_type"], "RIB2/3/4")

    def test_no_line_white_image_side(self):
        """白图 side → 0 条纵线 → 4 分（0 ≤ 1）"""
        score, details = self._run(_make_white_image(), "side")
        self.assertEqual(score, 4.0)
        self.assertEqual(details["groove_count"], 0)
        self.assertTrue(details["is_valid"])
        self.assertEqual(details["rib_type"], "RIB1/5")

    # ── 单条纵线 ────────────────────────────────────────────────────

    def test_single_line_center(self):
        """1 条纵线 center → count=1 → 4 分（1 ≤ 2）"""
        img = _make_vline_image(vband_cols=[(58, 58 + _NOMINAL_W)])
        score, details = self._run(img, "center")
        self.assertEqual(score, 4.0)
        self.assertEqual(details["groove_count"], 1)
        self.assertTrue(details["is_valid"])

    def test_single_line_side(self):
        """1 条纵线 side → count=1 → 4 分（1 ≤ 1）"""
        img = _make_vline_image(vband_cols=[(58, 58 + _NOMINAL_W)])
        score, details = self._run(img, "side")
        self.assertEqual(score, 4.0)
        self.assertEqual(details["groove_count"], 1)
        self.assertTrue(details["is_valid"])

    # ── 两条纵线 ────────────────────────────────────────────────────

    def test_two_lines_center_pass(self):
        """2 条纵线 center → count=2 → 4 分（2 ≤ 2，上限边界）"""
        img = _make_vline_image(vband_cols=[
            (20, 20 + _NOMINAL_W),
            (90, 90 + _NOMINAL_W),
        ])
        score, details = self._run(img, "center")
        self.assertEqual(score, 4.0)
        self.assertEqual(details["groove_count"], 2)
        self.assertTrue(details["is_valid"])

    def test_two_lines_side_fail(self):
        """2 条纵线 side → count=2 → 0 分（2 > 1）"""
        img = _make_vline_image(vband_cols=[
            (20, 20 + _NOMINAL_W),
            (90, 90 + _NOMINAL_W),
        ])
        score, details = self._run(img, "side")
        self.assertEqual(score, 0.0)
        self.assertEqual(details["groove_count"], 2)
        self.assertFalse(details["is_valid"])

    # ── 三条纵线 ────────────────────────────────────────────────────

    def test_three_lines_center_fail(self):
        """3 条纵线 center → count=3 → 0 分（3 > 2）"""
        img = _make_vline_image(vband_cols=[
            (15, 15 + _NOMINAL_W),   # 15-18，完全在 edge_margin(12px) 之外
            (54, 54 + _NOMINAL_W),
            (96, 96 + _NOMINAL_W),
        ])
        score, details = self._run(img, "center")
        self.assertEqual(score, 0.0)
        self.assertEqual(details["groove_count"], 3)
        self.assertFalse(details["is_valid"])

    # ── 返回结构验证 ────────────────────────────────────────────────

    def test_positions_are_sorted_ascending(self):
        """groove_positions 升序排列"""
        img = _make_vline_image(vband_cols=[
            (90, 90 + _NOMINAL_W),
            (20, 20 + _NOMINAL_W),
        ])
        _, details = self._run(img, "center")
        positions = details["groove_positions"]
        self.assertEqual(positions, sorted(positions))

    def test_positions_and_widths_same_length(self):
        """groove_positions 与 groove_widths 长度相同"""
        img = _make_vline_image(vband_cols=[
            (20, 20 + _NOMINAL_W),
            (90, 90 + _NOMINAL_W),
        ])
        _, details = self._run(img, "center")
        self.assertEqual(
            len(details["groove_positions"]),
            len(details["groove_widths"]),
        )

    def test_details_keys_present(self):
        """成功时 details 包含所有必需键"""
        img = _make_white_image()
        score, details = self._run(img, "center")
        required = {
            "rib_type", "groove_count", "groove_positions",
            "groove_widths", "is_valid", "score", "line_mask", "debug_image",
        }
        self.assertTrue(required.issubset(set(details.keys())))

    def test_debug_image_shape(self):
        """debug_image 形状与输入图像相同"""
        img = _make_white_image()
        _, details = self._run(img, "center")
        self.assertEqual(details["debug_image"].shape, img.shape)

    def test_line_mask_binary(self):
        """line_mask 只包含 0 和 255"""
        img = _make_vline_image(vband_cols=[(58, 58 + _NOMINAL_W)])
        _, details = self._run(img, "center")
        unique_vals = set(np.unique(details["line_mask"]).tolist())
        self.assertTrue(unique_vals.issubset({0, 255}))

    def test_image_type_case_insensitive(self):
        """image_type 大小写不敏感"""
        img = _make_white_image()
        score_lower, _ = self._run(img, "center")
        score_upper, _ = self._run(img, "CENTER")
        self.assertEqual(score_lower, score_upper)

    # ── 宽度无上限约束验证 ──────────────────────────────────────────

    def test_wide_line_above_nominal_still_counted(self):
        """宽度 > nominal (10px) 的线条 → 无上限约束，应计为 1 条纵沟"""
        # 10px 宽的暗带，nominal=4px，新规则 min_w=3px，无上限
        img = _make_vline_image(vband_cols=[(60, 70)])
        _, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 1,
                         "10px 宽线条（> nominal 4px）无上限约束时应被计为纵沟")

    # ── 左右边缘排除验证 ──────────────────────────────────────────

    def test_edge_lines_excluded(self):
        """
        左右边缘纵线（主沟残留）→ edge_margin 内，不计入纵向细沟

        模拟小图截取时左右两侧主沟切边残留：
        - 128px 宽图像，edge_margin_ratio=0.10 → 左右各 12px 被屏蔽
        - 左边带 (0, 12): 左边界内，应排除
        - 右边带 (116, 128): 右边界内，应排除
        - 中心无线条 → count=0 → score=4
        """
        # 128px 图像，默认 edge_margin_ratio=0.10 → edge_margin_px=12
        img = _make_vline_image(vband_cols=[(0, 12), (116, 128)])
        score, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 0,
                         "左右边缘纵线应被 edge_margin 排除，不应计入")
        self.assertEqual(score, 4.0,
                         "无有效纵线时应得满分")
        self.assertTrue(details["is_valid"])

    def test_edge_lines_excluded_side(self):
        """同上， side 类型边缘主沟残留不应被计入"""
        img = _make_vline_image(vband_cols=[(0, 12), (116, 128)])
        score, details = self._run(img, "side")
        self.assertEqual(details["groove_count"], 0)
        self.assertEqual(score, 4.0)

    def test_valid_central_line_not_affected_by_edge_exclusion(self):
        """中心区域的纵向线条不受边缘排除影响"""
        # 中心位置，远离边缘
        img = _make_vline_image(vband_cols=[(58, 58 + _NOMINAL_W)])
        score, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 1)
        self.assertEqual(score, 4.0)

    # ── 长度阈值与分段计数验证 ────────────────────────────────────

    def test_staggered_segments_counted_individually(self):
        """
        上下分离的 3 段纹理若各自宽度、长度达标，则应计为 3 条纵沟。

        该测试直接覆盖用户指定的业务规则：
        - 不再把多个分离段整体否决为 0 条
        - 每个分离连续段独立按宽度和长度阈值判定
        """
        img = np.full((128, 128, 3), 200, dtype=np.uint8)
        # 3 段各宽 4px，各高 30px（> 26px 最小长度），间隔 20px（> 4px 桥接阈值）
        segments = [
            (0,   30,  60, 64),
            (50,  80,  64, 68),
            (100, 128, 60, 64),
        ]
        for row_start, row_end, col_start, col_end in segments:
            for r in range(row_start, row_end):
                val = 20 if (r % 2 == 0) else 190
                img[r, col_start:col_end] = val

        score, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 3)
        self.assertEqual(score, 0.0)
        self.assertFalse(details["is_valid"])

    def test_continuous_groove_long_enough_is_counted(self):
        """单条连续纵沟只要宽度达标且长度充分，就应计数。"""
        img = _make_vline_image(vband_cols=[(58, 58 + _NOMINAL_W)])
        _, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 1)

    def test_top_half_segment_longer_than_one_fifth_is_counted(self):
        """
        宽度达标且长度超过图片宽度 1/5 的上半段短纵沟，应计为 1 条。
        """
        img = np.full((128, 128, 3), 200, dtype=np.uint8)
        for r in range(0, 55):
            val = 20 if (r % 2 == 0) else 190
            img[r, 62:66] = val   # 4px 宽，55 行（> 26px 最小长度）

        score, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 1)
        self.assertEqual(score, 4.0)
        self.assertTrue(details["is_valid"])

    def test_short_segment_below_min_height_not_counted(self):
        """宽度达标但高度不足最小阈值（0.12×128=16px）的短段，视为噪声不应计入。"""
        img = np.full((128, 128, 3), 200, dtype=np.uint8)
        for r in range(0, 9):
            val = 20 if (r % 2 == 0) else 190
            img[r, 62:66] = val   # 4px 宽，9 行（< 16px 最小阈值）

        _, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 0)

    def test_partial_groove_middle_gap_split_into_two_lines(self):
        """
        中间存在大断裂时，上下两段若分别达标，则应按 2 条纵沟计数。
        """
        img = np.full((128, 128, 3), 200, dtype=np.uint8)
        for seg_rows in [(5, 46), (80, 128)]:
            start, end = seg_rows
            for r in range(start, end):
                val = 20 if (r % 2 == 0) else 190
                img[r, 62:66] = val   # 4px 宽

        score, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 2)
        self.assertEqual(score, 4.0)
        self.assertTrue(details["is_valid"])


if _HAS_CV2:
    def _make_slanted_line_image(
        h: int = 128,
        w: int = 128,
        x_center_top: int = 34,
        angle_deg: float = 0.0,
        width: int = 4,
    ) -> "np.ndarray":
        """
        在亮色背景上绘制偏转 angle_deg（从竖直方向向右倾）的纵向线条。

        使用与 _make_vline_image 相同的交替明暗行技术保证自适应二值化检测。
        angle_deg=0 → 纯竖直；angle_deg=30 → 主轴偏竖直 30°。
        """
        img = np.full((h, w, 3), 200, dtype=np.uint8)
        import math
        tan_a = math.tan(math.radians(angle_deg))
        for r in range(h):
            cx  = int(round(x_center_top + r * tan_a))
            c_l = max(0, cx - width // 2)
            c_r = min(w, c_l + width)
            if c_l < c_r:
                val = 20 if (r % 2 == 0) else 190
                img[r, c_l:c_r] = val
        return img


@unittest.skipUnless(_HAS_CV2, "需要 numpy 和 opencv-python")
class TestLongitudinalGrooveAngleFilter(unittest.TestCase):
    """
    验证纵向线条的角度过滤逻辑（±30° 范围）。

    业务规则：现实纵沟可能轻微倾斜，允许偏离竖直方向 ≤30° 的线条计为纵沟。
    超过 30° 的连通域应被切割为极短子段并过滤，不计入纵沟数量。

    实现方式：对每行 center_x 做 7 点滑动均值后，检测相邻行坡度是否超过阈值；
    超过则在该行切割，仅保留"近竖直子段"（单条斜线若每行均超标则全部被切碎）。
    """

    def _run(self, img, image_type, max_angle_deg=30.0):
        from algorithms.detection.longitudinal_groove import detect_longitudinal_grooves
        return detect_longitudinal_grooves(
            img, image_type,
            groove_width_mm=_GROOVE_WMM,
            pixel_per_mm=_PIXEL_PER_MM,
            max_angle_deg=max_angle_deg,
        )

    def test_vertical_line_passes_angle_filter(self):
        """完全竖直的线条（0°）→ 应通过角度过滤，count=1"""
        img = _make_slanted_line_image(angle_deg=0.0, x_center_top=64, width=4)
        score, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 1)
        self.assertEqual(score, 4.0)

    def test_25deg_slant_passes_angle_filter(self):
        """25° 倾斜线条（< 30°）→ 应通过角度过滤，count=1"""
        img = _make_slanted_line_image(angle_deg=25.0, x_center_top=34, width=4)
        score, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 1,
                         "25° 倾斜线条应视为有效纵沟（< 30° 限制）")
        self.assertEqual(score, 4.0)

    def test_35deg_slant_fails_angle_filter(self):
        """35° 倾斜线条（> 30°）→ 应被角度过滤排除，count=0"""
        img = _make_slanted_line_image(angle_deg=35.0, x_center_top=20, width=4)
        score, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 0,
                         "35° 倾斜线条应被角度过滤排除（> 30° 限制）")
        self.assertEqual(score, 4.0)   # count=0 ≤ 2 → 满分

    def test_slanted_groove_side_type(self):
        """25° 倾斜线条，side 类型 → count=1 → 4 分（1 ≤ 1）"""
        img = _make_slanted_line_image(angle_deg=25.0, x_center_top=34, width=4)
        score, details = self._run(img, "side")
        self.assertEqual(details["groove_count"], 1)
        self.assertEqual(score, 4.0)

    def test_custom_angle_threshold_respected(self):
        """将 max_angle_deg 提高到 40°，原本被拒的 35° 线条应被接受"""
        img = _make_slanted_line_image(angle_deg=35.0, x_center_top=20, width=4)
        score, details = self._run(img, "center", max_angle_deg=40.0)
        self.assertEqual(details["groove_count"], 1,
                         "max_angle_deg=40 时 35° 倾斜线条应被接受")

    def test_vertical_connected_to_steep_diagonals_is_detected(self):
        """
        核心业务场景：竖线通过两端陡斜线（约 60°）形成一个连通域（类 Z 形）。

        旧算法（PCA 全局角度）：整段角度被斜线拉偏，超过 30° 而被整体拒绝。
        新算法（逐行坡度切割）：在竖-斜交界处切断，竖直子段独立满足高度/宽度
        条件而被正确计为 1 条纵沟。
        """
        import math
        img = np.full((128, 128, 3), 200, dtype=np.uint8)

        # 顶部斜线：从 (col=100, row=0) 以 -60° 斜向左下方，画 25 行
        tan60 = math.tan(math.radians(60))
        for r in range(0, 25):
            cx  = int(round(100 - r * tan60))   # 向左偏移
            c_l = max(0, cx - 3)
            c_r = min(128, c_l + 7)             # 宽约 7px（斜线较粗）
            val = 20 if (r % 2 == 0) else 190
            img[r, c_l:c_r] = val

        # 中间竖线：col=57~60（宽 4px），rows 25~90（高 66px >> min 26px）
        for r in range(25, 91):
            val = 20 if (r % 2 == 0) else 190
            img[r, 57:61] = val

        # 底部斜线：从 (col=57, row=90) 向右下方以 60° 斜出，画 30 行
        for r in range(90, 120):
            cx  = int(round(57 + (r - 90) * tan60))
            c_l = max(0, cx - 3)
            c_r = min(128, c_l + 7)
            val = 20 if (r % 2 == 0) else 190
            img[r, c_l:c_r] = val

        score, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 1,
                         "竖线子段应从 Z 形连通域中被提取为 1 条纵沟")
        self.assertEqual(score, 4.0)
        self.assertTrue(details["is_valid"])

    def test_two_short_vertical_grooves_connected_by_diagonals_detected(self):
        """
        两条短竖向纵沟，各被陡斜线（>30°）拼接成一个 N/Z 型复杂结构。

        每条竖直子段高度约 20px（< 1/5 图宽=26px），但父连通域高度 >> 26px，
        因此算法应使用宽松阈值（×0.65 ≈ 17px）提取子段，计为 2 条纵沟。

        测试目的：防止回归到"子段高度 < 26px 一律拒绝"的逻辑。
        """
        import math
        img = np.full((128, 128, 3), 200, dtype=np.uint8)

        # 绘制辅助：按列范围在 rows 中画竖带
        def draw_vband(row_start, row_end, col_l, col_r):
            for r in range(row_start, row_end):
                val = 20 if (r % 2 == 0) else 190
                img[r, col_l:col_r] = val

        # 绘制斜线段：以 (col_start, row_start) 为起点，按 dx_per_row 斜率画 n_rows 行
        def draw_diag(row_start, n_rows, col_start, dx_per_row, width=5):
            for i in range(n_rows):
                r  = row_start + i
                cx = int(round(col_start + i * dx_per_row))
                c_l = max(0, cx - width // 2)
                c_r = min(128, c_l + width)
                val = 20 if (r % 2 == 0) else 190
                img[r, c_l:c_r] = val

        tan60 = math.tan(math.radians(60))

        # 结构：
        #   rows  0-24 : 顶部陡斜（向左下，60°），从 col≈100 到 col≈57
        #   rows 25-44 : 第一段近竖直纵沟（col 55-59，高 20px）
        #   rows 45-64 : 中部陡斜（向右下，60°），从 col≈57 到 col≈74
        #   rows 65-84 : 第二段近竖直纵沟（col 72-76，高 20px）
        #   rows 85-110: 底部陡斜（向左下，60°）

        draw_diag(0,  25, 100, -tan60)       # 顶部斜线
        draw_vband(25, 45, 55, 59)            # 第一段竖纵沟（20px）
        draw_diag(45, 20, 57, +tan60)        # 中部斜线
        draw_vband(65, 85, 72, 76)            # 第二段竖纵沟（20px）
        draw_diag(85, 26, 74, -tan60)        # 底部斜线

        score, details = self._run(img, "center")
        self.assertEqual(details["groove_count"], 2,
                         "两条短竖直子段（各约 20px）应从复杂连通域中被分别提取为 2 条纵沟")
        self.assertEqual(score, 4.0)
        self.assertTrue(details["is_valid"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
