# -*- coding: utf-8 -*-
"""
stitch_and_resize 纯函数单元测试
"""

import pytest
from PIL import Image
from algorithms.stitching.vertical_stitch import stitch_and_resize


class TestStitchAndResize:
    """stitch_and_resize 纯函数单元测试"""

    def test_stitch_and_resize_basic(self):
        """基本功能测试"""
        img = Image.new('RGB', (100, 50), color='red')
        result = stitch_and_resize(img, 3, (200, 300))
        assert result.size == (200, 300)

    def test_stitch_and_resize_single_stitch(self):
        """单次拼接测试"""
        img = Image.new('RGB', (100, 50), color='blue')
        result = stitch_and_resize(img, 1, (100, 50))
        assert result.size == (100, 50)

    def test_stitch_and_resize_multi_stitch(self):
        """多次拼接测试"""
        img = Image.new('RGB', (100, 50), color='green')
        result = stitch_and_resize(img, 5, (100, 250))
        assert result.size == (100, 250)

    def test_stitch_and_resize_with_pattern(self):
        """带图案图片的拼接验证"""
        # 创建带渐变的图片
        img = Image.new('RGB', (100, 50))
        for i in range(50):
            for j in range(100):
                img.putpixel((j, i), (i * 5, j * 2, 100))

        result = stitch_and_resize(img, 3, (200, 150))
        assert result.size == (200, 150)
        # 验证拼接后图案存在：原图高度 50，拼接 3 次后高度 150
        # 验证顶部、中部、底部都有正确的图案
        pixel_top = result.getpixel((50, 10))  # 顶部区域
        pixel_middle = result.getpixel((50, 75))  # 中部区域
        pixel_bottom = result.getpixel((50, 140))  # 底部区域
        # 由于 resize 操作，像素值会进行插值，但三个区域的像素应该有差异
        # 验证三个位置的像素值不完全相同
        assert pixel_top != pixel_middle or pixel_middle != pixel_bottom

    def test_stitch_and_resize_invalid_stitch_zero(self):
        """stitch_count=0 应该抛出 ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, 0, (200, 300))

    def test_stitch_and_resize_invalid_stitch_negative(self):
        """stitch_count<0 应该抛出 ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, -1, (200, 300))

    def test_stitch_and_resize_invalid_target_size_single(self):
        """target_size 单元素应该抛出 ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, 3, (100,))

    def test_stitch_and_resize_invalid_target_size_triple(self):
        """target_size 三元素应该抛出 ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, 3, (100, 100, 100))

    def test_stitch_and_resize_invalid_target_size_string(self):
        """target_size 字符串应该抛出 ValueError"""
        img = Image.new('RGB', (100, 50))
        with pytest.raises(ValueError):
            stitch_and_resize(img, 3, "200x300")
