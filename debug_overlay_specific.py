#!/usr/bin/env python3
"""
调试 overlay_decoration 的具体问题
"""

import cv2
import numpy as np
from src.core.operation.image_operation import overlay_decoration, apply_opacity

def main():
    # 创建简单的测试数据
    base_image = np.zeros((10, 10, 3), dtype=np.uint8)  # 黑色基础
    base_image[:, :, 2] = 255  # 红色

    decoration = np.ones((10, 3, 3), dtype=np.uint8) * 255  # 白色装饰
    decoration_bgra = apply_opacity(decoration, 128)  # 50% 透明度

    print(f"基础图像: {base_image.shape}")
    print(f"装饰图像: {decoration_bgra.shape}")
    print(f"装饰alpha: {decoration_bgra[0,0,3]}")

    # 应用覆盖
    result = overlay_decoration(base_image, decoration_bgra, decoration_bgra)

    print(f"结果图像: {result.shape}")
    print(f"结果左侧3像素: {result[0, :3]}")
    print(f"结果右侧3像素: {result[0, -3:]}")
    print(f"结果中间: {result[0, 3:7]}")

    # 手动计算期望值
    # 左侧: 白色*0.5 + 红色*0.5 = [127, 127, 255]
    expected_left = np.array([127, 127, 255])
    actual_left = result[0, 0]

    print(f"期望左侧: {expected_left}")
    print(f"实际左侧: {actual_left}")

    if np.allclose(actual_left, expected_left, atol=2):
        print("✅ 左侧混合正确")
    else:
        print("❌ 左侧混合错误")

if __name__ == "__main__":
    main()