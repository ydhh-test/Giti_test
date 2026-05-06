# -*- coding: utf-8 -*-
"""
垂直拼接算法单元测试（新架构 dev2）

测试目标：src.core.stitching.vertical_stitch.stitch_and_resize
主要变更：import 路径 algorithms.stitching.* → src.core.stitching.*
"""

import sys
import pathlib
import pytest

_ROOT = pathlib.Path(__file__).parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PIL import Image
from src.core.stitching.vertical_stitch import stitch_and_resize


class TestStitchAndResize:
    """stitch_and_resize 纯函数单元测试"""

    def test_basic(self):
        """基本功能：输出尺寸正确"""
        img = Image.new('RGB', (100, 50), color='red')
        result = stitch_and_resize(img, 3, (200, 300))
        assert result.size == (200, 300)

    def test_single_stitch(self):
        """单次拼接：输出尺寸与目标一致"""
        img = Image.new('RGB', (100, 50), color='blue')
        result = stitch_and_resize(img, 1, (100, 50))
        assert result.size == (100, 50)

    def test_multi_stitch(self):
        """多次拼接：输出尺寸正确"""
        img = Image.new('RGB', (100, 50), color='green')
        result = stitch_and_resize(img, 5, (100, 250))
        assert result.size == (100, 250)

    def test_with_gradient_pattern(self):
        """带渐变图案的拼接：顶/中/底像素值有差异"""
        img = Image.new('RGB', (100, 50))
        for i in range(50):
            for j in range(100):
                img.putpixel((j, i), (i * 5, j * 2, 100))
        result = stitch_and_resize(img, 3, (200, 150))
        assert result.size == (200, 150)
        p_top    = result.getpixel((50, 10))
        p_middle = result.getpixel((50, 75))
        p_bottom = result.getpixel((50, 140))
        # resize 会插值，但三区域不应完全相同
        assert p_top != p_middle or p_middle != p_bottom

    def test_invalid_stitch_zero(self):
        """stitch_count==0 → ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, 0, (200, 300))

    def test_invalid_stitch_negative(self):
        """stitch_count<0 → ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, -1, (200, 300))

    def test_invalid_target_size_single_element(self):
        """target_size 单元素 → ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, 3, (100,))

    def test_invalid_target_size_triple(self):
        """target_size 三元素 → ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, 3, (100, 100, 100))

    def test_invalid_target_size_string(self):
        """target_size 字符串 → ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, 3, "200x300")
