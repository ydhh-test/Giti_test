#!/usr/bin/env python3
"""
验证 overlay_decoration 实现的正确性
"""

import cv2
import numpy as np
from src.core.operation.image_operation import overlay_decoration, apply_opacity
from src.utils.image_utils import base64_to_ndarray, ndarray_to_base64

def manual_alpha_blend(base_image, decoration_bgra):
    """手动实现alpha混合"""
    if len(decoration_bgra.shape) != 4:
        return base_image.copy()

    h, w = base_image.shape[:2]
    dec_h, dec_w = decoration_bgra.shape[:2]

    if dec_h != h:
        raise ValueError("高度不匹配")

    result = base_image.copy().astype(np.float32)

    # 提取装饰的RGB和alpha
    dec_rgb = decoration_bgra[:, :, :3].astype(np.float32)
    dec_alpha = decoration_bgra[:, :, 3] / 255.0

    # 左侧混合
    result[:, :dec_w] = (
        dec_rgb * dec_alpha[:, :, np.newaxis] +
        result[:, :dec_w] * (1 - dec_alpha[:, :, np.newaxis])
    )

    # 右侧混合
    result[:, w-dec_w:] = (
        dec_rgb * dec_alpha[:, :, np.newaxis] +
        result[:, w-dec_w:] * (1 - dec_alpha[:, :, np.newaxis])
    )

    return np.clip(result, 0, 255).astype(np.uint8)

def main():
    # 创建测试数据
    base_image = np.random.randint(0, 256, (100, 500, 3), dtype=np.uint8)
    decoration = np.ones((100, 100, 3), dtype=np.uint8) * 200  # 灰色装饰

    # 应用透明度
    decoration_bgra = apply_opacity(decoration, 128)  # 50% 透明度

    # 方法1: 使用我们的 overlay_decoration
    result1 = overlay_decoration(base_image, decoration_bgra, decoration_bgra)

    # 方法2: 手动alpha混合
    result2 = manual_alpha_blend(base_image, decoration_bgra)

    # 比较结果
    difference = np.abs(result1.astype(np.float32) - result2.astype(np.float32))
    max_diff = np.max(difference)
    mean_diff = np.mean(difference)

    print(f"最大差异: {max_diff}")
    print(f"平均差异: {mean_diff}")

    if max_diff < 1.0 and mean_diff < 0.1:
        print("✅ overlay_decoration 实现正确！")
    else:
        print("❌ overlay_decoration 实现有问题")

    # 保存结果用于视觉比较
    cv2.imwrite('.results/overlay_validation_method1.png', result1)
    cv2.imwrite('.results/overlay_validation_method2.png', result2)

if __name__ == "__main__":
    main()