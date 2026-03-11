"""
海陆比评分规则单元测试
"""

import pytest
import numpy as np
import cv2
from rules.scoring.land_sea_ratio import (
    compute_land_sea_ratio,
    compute_black_area,
    compute_gray_area
)


def test_compute_black_area():
    """测试黑色区域计算"""
    # 创建测试图像: 上半部分黑色(30), 下半部分白色(255)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:50, :] = 30  # 黑色
    img[50:, :] = 255  # 白色

    black_area = compute_black_area(img)

    # 黑色区域应该是5000像素 (50*100)
    assert black_area == 5000


def test_compute_gray_area():
    """测试灰色区域计算"""
    # 创建测试图像: 上半部分灰色(100), 下半部分白色(255)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:50, :] = 100  # 灰色
    img[50:, :] = 255  # 白色

    gray_area = compute_gray_area(img)

    # 灰色区域应该是5000像素
    assert gray_area == 5000


def test_compute_land_sea_ratio_excellent():
    """测试海陆比计算 - 优秀等级"""
    # 创建测试图像: 30%黑色+灰色
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:30, :] = 30  # 30%黑色
    img[30:, :] = 255  # 70%白色

    conf = {
        "target_min": 28.0,
        "target_max": 35.0,
        "margin": 5.0
    }

    score, details = compute_land_sea_ratio(img, conf)

    assert score == 2  # 优秀
    assert details["ratio_value"] >= 28.0 and details["ratio_value"] <= 35.0


def test_compute_land_sea_ratio_pass():
    """测试海陆比计算 - 合格等级"""
    # 创建测试图像: 25%黑色+灰色 (在容差范围内)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:25, :] = 30  # 25%黑色
    img[25:, :] = 255  # 75%白色

    conf = {
        "target_min": 28.0,
        "target_max": 35.0,
        "margin": 5.0
    }

    score, details = compute_land_sea_ratio(img, conf)

    assert score == 1  # 合格
    assert details["ratio_value"] >= 23.0 and details["ratio_value"] < 28.0


def test_compute_land_sea_ratio_fail():
    """测试海陆比计算 - 不合格等级"""
    # 创建测试图像: 10%黑色+灰色 (超出容差范围)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:10, :] = 30  # 10%黑色
    img[10:, :] = 255  # 90%白色

    conf = {
        "target_min": 28.0,
        "target_max": 35.0,
        "margin": 5.0
    }

    score, details = compute_land_sea_ratio(img, conf)

    assert score == 0  # 不合格
    assert details["ratio_value"] < 23.0


def test_compute_land_sea_ratio_with_actual_image():
    """测试海陆比计算 - 使用实际图片"""
    import os

    # 使用测试数据集中的图片
    test_image_path = "tests/datasets/horizontal_stitch/center/0.png"

    if os.path.exists(test_image_path):
        img = cv2.imread(test_image_path)
        assert img is not None, f"Failed to load image: {test_image_path}"

        conf = {
            "target_min": 28.0,
            "target_max": 35.0,
            "margin": 5.0
        }

        score, details = compute_land_sea_ratio(img, conf)

        assert score in [0, 1, 2], f"Invalid score: {score}"
        assert "ratio_value" in details
        assert "black_area" in details
        assert "gray_area" in details
        assert details["black_area"] >= 0
        assert details["gray_area"] >= 0
    else:
        pytest.skip(f"Test image not found: {test_image_path}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
