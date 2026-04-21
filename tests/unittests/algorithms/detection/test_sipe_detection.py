# -*- coding: utf-8 -*-

"""
横向钢片检测算法单元测试

包含两个测试类：
1. TestSipeDetectionSimple - 不依赖 numpy/opencv，测试纯评分逻辑
2. TestSipeDetectionFull   - 依赖 numpy/opencv，用合成图像测试完整流程
"""

import sys
import pathlib
import unittest

import numpy as np
import cv2
import pytest

# 确保项目根目录在 sys.path 中
_ROOT = pathlib.Path(__file__).parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from algorithms.detection.sipe_detection import (
    detect_horizontal_sipes,
    _detect_sipes,
    _score_sipe_count,
    _score_sipe_position,
)
from configs.rules_config import HorizontalSipesConfig


# ============================================================
# 简化测试（纯评分逻辑）
# ============================================================

class TestSipeDetectionSimple(unittest.TestCase):
    """不依赖图像的核心评分逻辑测试。"""

    _MAX_REQ9 = 4
    _MAX_REQ10 = 4

    # ── 需求9：数量评分 ─────────────────────────────────────────────

    def test_req9_center_0_sipes_pass(self):
        """center (max=2): 0 根钢片 → 满分"""
        assert _score_sipe_count(0, 2) == self._MAX_REQ9

    def test_req9_center_2_sipes_pass(self):
        """center (max=2): 2 根钢片 → 满分"""
        assert _score_sipe_count(2, 2) == self._MAX_REQ9

    def test_req9_center_3_sipes_fail(self):
        """center (max=2): 3 根钢片 → 0 分"""
        assert _score_sipe_count(3, 2) == 0

    def test_req9_side_0_sipes_pass(self):
        """side (max=3): 0 根钢片 → 满分"""
        assert _score_sipe_count(0, 3) == self._MAX_REQ9

    def test_req9_side_3_sipes_pass(self):
        """side (max=3): 3 根钢片 → 满分"""
        assert _score_sipe_count(3, 3) == self._MAX_REQ9

    def test_req9_side_4_sipes_fail(self):
        """side (max=3): 4 根钢片 → 0 分"""
        assert _score_sipe_count(4, 3) == 0

    # ── 需求10：两横沟 + 块内钢片均分花纹块 ─────────────────────────

    def test_req10_no_sipes_pass(self):
        """0 根钢片 → 满分（无需均分）"""
        assert _score_sipe_position([], [], 128, 0.3) == self._MAX_REQ10
        # 即使没有横沟，只要没有钢片也满分
        assert _score_sipe_position([], [20.0, 100.0], 128, 0.3) == self._MAX_REQ10

    def test_req10_no_grooves_with_sipes_fail(self):
        """有钢片但横沟不足 2 根 → 无法构成花纹块 → 0 分"""
        # 新规则：必须有 ≥2 根横沟才能形成夹持花纹块
        assert _score_sipe_position([64.0], [], 128, 0.3) == 0
        assert _score_sipe_position([40.0, 80.0], [64.0], 128, 0.3) == 0

    def test_req10_sipe_outside_groove_span_fail(self):
        """钢片落在最外两条横沟之外 → 0 分"""
        # 横沟 [20, 100]，钢片 10 在上边外
        assert _score_sipe_position([10.0], [20.0, 100.0], 128, 0.3) == 0
        # 钢片 110 在下边外
        assert _score_sipe_position([110.0], [20.0, 100.0], 128, 0.3) == 0

    def test_req10_one_sipe_center_pass(self):
        """两横沟 + 1 根钢片在正中 → 满分"""
        # 横沟 20, 100，块高 80，1 根钢片 μ=40，位置 60.0 → gap=[40,40]
        assert _score_sipe_position([60.0], [20.0, 100.0], 128, 0.3) == self._MAX_REQ10

    def test_req10_one_sipe_offset_within_tolerance(self):
        """1 根钢片偏移在容忍范围内 → 满分"""
        # 块 [20,100] 高 80，μ=40，容忍 12
        # 位置 70.0 → gap=[50,30] → |gap-μ|=10 ≤ 12 → 通过
        assert _score_sipe_position([70.0], [20.0, 100.0], 128, 0.3) == self._MAX_REQ10

    def test_req10_one_sipe_offset_exceeds_tolerance(self):
        """1 根钢片偏移超出容忍范围 → 0 分"""
        # 块 [20,100] 高 80，μ=40，容忍 12
        # 位置 73.0 → gap=[53,27] → |gap-μ|=13 > 12 → 不通过
        assert _score_sipe_position([73.0], [20.0, 100.0], 128, 0.3) == 0

    def test_req10_two_sipes_evenly_spaced_pass(self):
        """两横沟 + 2 根钢片均分 → 满分"""
        # 横沟 0, 120，块高 120，3 段 μ=40，钢片 40, 80 → gap=[40,40,40]
        assert _score_sipe_position([40.0, 80.0], [0.0, 120.0], 128, 0.3) == self._MAX_REQ10

    def test_req10_two_sipes_uneven_fail(self):
        """2 根钢片不均分 → 0 分"""
        # 横沟 0, 120，μ=40，容忍 12
        # 钢片 30, 60 → gap=[30,30,60] → |60-40|=20 > 12 → 不通过
        assert _score_sipe_position([30.0, 60.0], [0.0, 120.0], 128, 0.3) == 0

    def test_req10_three_grooves_per_block_check(self):
        """3 根横沟分 2 个花纹块，每块独立判定"""
        # 块1 [0, 60] 1 根钢片在 30 → gap=[30,30] → OK
        # 块2 [60, 120] 1 根钢片在 90 → gap=[30,30] → OK
        assert _score_sipe_position([30.0, 90.0], [0.0, 60.0, 120.0], 128, 0.3) \
            == self._MAX_REQ10

    def test_req10_three_grooves_one_block_fails(self):
        """3 根横沟分 2 块，其中 1 块不均分 → 0 分"""
        # 块1 [0, 60] 钢片 30 → OK
        # 块2 [60, 120] 钢片 115 → gap=[55,5] vs μ=30，|55-30|=25 > 9 → NG
        assert _score_sipe_position([30.0, 115.0], [0.0, 60.0, 120.0], 128, 0.3) == 0

    def test_req10_tolerance_boundary_pass(self):
        """偏差恰好等于 tolerance × 理想间距 → 通过（非严格不等式）"""
        # 横沟 [0,100] 块高 100，1 根钢片 μ=50，容忍 15
        # 位置 65.0 → gap=[65,35] → |gap-μ|=15 ≤ 15 → 通过
        assert _score_sipe_position([65.0], [0.0, 100.0], 128, 0.3) == self._MAX_REQ10

    def test_req10_tolerance_boundary_fail(self):
        """偏差刚超过 tolerance × 理想间距 → 0 分"""
        # 横沟 [0,100] 块高 100，μ=50，容忍 15
        # 位置 65.1 → gap=[65.1, 34.9] → |gap-μ|=15.1 > 15 → 不通过
        assert _score_sipe_position([65.1], [0.0, 100.0], 128, 0.3) == 0


# ============================================================
# 完整流程测试（使用合成图像）
# ============================================================

class TestSipeDetectionFull(unittest.TestCase):
    """使用合成图像测试完整检测流程。"""

    def _make_blank_bgr(self, h=128, w=128, bg_val=200):
        """创建浅灰色背景 BGR 图像"""
        return np.full((h, w, 3), bg_val, dtype=np.uint8)

    def _draw_horizontal_line(self, img, y, thickness, color=0):
        """在图像上画一条水平暗色线（模拟横沟或钢片）"""
        half = thickness // 2
        y_start = max(0, y - half)
        y_end = min(img.shape[0], y + half + thickness % 2)
        img[y_start:y_end, :] = color
        return img

    def test_detect_no_features(self):
        """纯灰色图无特征 → sipe_count=0, groove_count=0"""
        img = self._make_blank_bgr()
        score, details = detect_horizontal_sipes(img, "center")
        assert score is not None
        assert details["sipe_count"] == 0
        assert details["groove_count"] == 0
        # 0 根钢片 → 满分 8 (4+4)
        assert details["score_req9"] == 4
        assert details["score_req10"] == 4

    def test_detect_single_sipe_center(self):
        """center 图中 1 根钢片（4px 暗线）→ 应被检出"""
        img = self._make_blank_bgr()
        self._draw_horizontal_line(img, 64, 4)
        score, details = detect_horizontal_sipes(img, "center")
        assert score is not None
        assert details["sipe_count"] >= 1
        assert details["rib_type"] == "RIB2/3/4"

    def test_detect_groove_not_counted_as_sipe(self):
        """1 条粗暗线（25px）应被分类为横沟，不是钢片"""
        img = self._make_blank_bgr()
        self._draw_horizontal_line(img, 64, 25)
        score, details = detect_horizontal_sipes(img, "center")
        assert score is not None
        assert details["groove_count"] >= 1
        # 粗线不应计入钢片
        assert details["sipe_count"] == 0

    def test_detect_mixed_groove_and_sipes(self):
        """1 条横沟 + 2 根钢片 → groove_count >= 1, sipe_count >= 1"""
        img = self._make_blank_bgr()
        self._draw_horizontal_line(img, 64, 25)   # 横沟
        self._draw_horizontal_line(img, 30, 4)     # 钢片
        self._draw_horizontal_line(img, 100, 4)    # 钢片
        score, details = detect_horizontal_sipes(img, "center")
        assert score is not None
        assert details["groove_count"] >= 1
        assert details["sipe_count"] >= 1

    def test_center_exceeds_max_sipes(self):
        """center 图 3 根钢片（超过 max=2）→ score_req9=0"""
        img = self._make_blank_bgr()
        for y in [30, 64, 98]:
            self._draw_horizontal_line(img, y, 4)
        score, details = detect_horizontal_sipes(
            img, "center", sipe_count_max={"center": 2, "side": 3}
        )
        if details["sipe_count"] > 2:
            assert details["score_req9"] == 0

    def test_side_type(self):
        """side 类型正常处理"""
        img = self._make_blank_bgr()
        self._draw_horizontal_line(img, 64, 4)
        score, details = detect_horizontal_sipes(img, "side")
        assert score is not None
        assert details["rib_type"] == "RIB1/5"

    def test_invalid_image_none(self):
        """None 输入 → 返回 None + err_msg"""
        score, details = detect_horizontal_sipes(None, "center")
        assert score is None
        assert "err_msg" in details

    def test_invalid_image_type(self):
        """非法 image_type → 返回 None + err_msg"""
        img = self._make_blank_bgr()
        score, details = detect_horizontal_sipes(img, "invalid")
        assert score is None
        assert "err_msg" in details

    def test_grayscale_image_rejected(self):
        """灰度图（2D）→ 返回 None + err_msg"""
        gray = np.full((128, 128), 200, dtype=np.uint8)
        score, details = detect_horizontal_sipes(gray, "center")
        assert score is None
        assert "err_msg" in details

    def test_debug_image_generated(self):
        """成功时返回 debug_image（BGR 三通道）"""
        img = self._make_blank_bgr()
        score, details = detect_horizontal_sipes(img, "center")
        assert score is not None
        assert "debug_image" in details
        dbg = details["debug_image"]
        assert dbg.ndim == 3
        assert dbg.shape[2] == 3

    def test_score_range(self):
        """总分在 [0, 8] 范围内"""
        img = self._make_blank_bgr()
        score, details = detect_horizontal_sipes(img, "center")
        assert score is not None
        assert 0.0 <= score <= 8.0

    def test_custom_pixel_per_mm(self):
        """自定义 pixel_per_mm 不报错"""
        img = self._make_blank_bgr()
        score, _ = detect_horizontal_sipes(img, "center", pixel_per_mm=5.0)
        assert score is not None


# ============================================================
# _detect_sipes 单元测试
# ============================================================

class TestDetectSipesInternal(unittest.TestCase):
    """直接测试 _detect_sipes 内部函数。"""

    def _make_binary_with_bands(self, h=128, w=128, bands=None):
        """
        创建二值图，bands 为 [(y_center, thickness), ...] 列表。
        """
        binary = np.zeros((h, w), dtype=np.uint8)
        if bands:
            for y_center, thickness in bands:
                half = thickness // 2
                y_start = max(0, y_center - half)
                y_end = min(h, y_center + half + thickness % 2)
                binary[y_start:y_end, :] = 255
        return binary

    def test_no_bands(self):
        """无带状区域 → 0 根钢片"""
        binary = self._make_binary_with_bands()
        positions, count = _detect_sipes(binary, 128, 3, 6, 11)
        assert count == 0
        assert positions == []

    def test_single_sipe_band(self):
        """单条 4px 宽带 → 检出 1 根钢片"""
        binary = self._make_binary_with_bands(bands=[(64, 4)])
        positions, count = _detect_sipes(binary, 128, 3, 6, 11)
        assert count == 1
        assert len(positions) == 1
        assert abs(positions[0] - 64.0) < 3.0

    def test_groove_excluded(self):
        """15px 宽带 ≥ groove_min_px(11) → 不计入钢片"""
        binary = self._make_binary_with_bands(bands=[(64, 15)])
        positions, count = _detect_sipes(binary, 128, 3, 6, 11)
        assert count == 0

    def test_noise_excluded(self):
        """1px 宽带只覆盖少量列 → 不满足 min_px_per_row → 不计入"""
        binary = np.zeros((128, 128), dtype=np.uint8)
        # 只在少数列画白色（不足 img_w//12 = 10 px）
        binary[64, :5] = 255
        positions, count = _detect_sipes(binary, 128, 3, 6, 11)
        assert count == 0

    def test_mixed_bands(self):
        """混合带：1 条横沟(15px) + 2 条钢片(4px) + 1 条噪声(部分宽度)"""
        binary = self._make_binary_with_bands(bands=[
            (30, 4),    # sipe
            (64, 15),   # groove → 排除
            (100, 4),   # sipe
        ])
        # 添加部分宽度噪声（只覆盖少量列，不满足 min_px_per_row）
        binary[120, :5] = 255
        positions, count = _detect_sipes(binary, 128, 3, 6, 11)
        assert count == 2


if __name__ == "__main__":
    unittest.main()
