#!/usr/bin/env python3
"""
调查 BGRA 到 BGR 转换的最佳方法
"""

import cv2
import numpy as np

def bgra_to_bgr_with_background(bgra, background=(0, 0, 0)):
    """
    将BGRA转换为BGR，使用指定背景色保持视觉外观

    Args:
        bgra: BGRA图像 (H, W, 4)
        background: 背景色 (B, G, R)，默认黑色

    Returns:
        bgr: BGR图像 (H, W, 3)
    """
    if len(bgra.shape) != 3 or bgra.shape[2] != 4:
        return bgra  # 已经是BGR或其他格式

    # 分离通道
    b, g, r, a = cv2.split(bgra.astype(np.float32))
    alpha = a / 255.0

    bg_b, bg_g, bg_r = background

    # 应用alpha混合公式
    b_result = b * alpha + bg_b * (1 - alpha)
    g_result = g * alpha + bg_g * (1 - alpha)
    r_result = r * alpha + bg_r * (1 - alpha)

    return cv2.merge([b_result, g_result, r_result]).astype(np.uint8)

def create_example():
    """创建示例图像"""
    # 创建一个简单的测试图像
    height, width = 100, 200
    bgra = np.zeros((height, width, 4), dtype=np.uint8)

    # 左半部分：红色，alpha从0到255渐变
    for x in range(width//2):
        bgra[:, x, 2] = 255  # 红色
        bgra[:, x, 3] = int(255 * x / (width//2))  # alpha渐变

    # 右半部分：蓝色，固定alpha=128 (50%)
    bgra[:, width//2:, 0] = 255  # 蓝色
    bgra[:, width//2:, 3] = 128  # 50% 透明度

    return bgra

def main():
    # 创建示例
    example_bgra = create_example()
    print(f"示例BGRA图像: {example_bgra.shape}")

    # 使用不同背景色转换
    black_bg = bgra_to_bgr_with_background(example_bgra, (0, 0, 0))      # 黑色背景
    white_bg = bgra_to_bgr_with_background(example_bgra, (255, 255, 255)) # 白色背景
    gray_bg = bgra_to_bgr_with_background(example_bgra, (128, 128, 128))  # 灰色背景

    # 保存结果
    cv2.imwrite('.results/example_bgra.png', example_bgra)
    cv2.imwrite('.results/example_black_bg.png', black_bg)
    cv2.imwrite('.results/example_white_bg.png', white_bg)
    cv2.imwrite('.results/example_gray_bg.png', gray_bg)

    print("✅ 示例图像已生成:")
    print("  - .results/example_bgra.png (原始BGRA，可用支持alpha的查看器查看)")
    print("  - .results/example_black_bg.png (黑色背景)")
    print("  - .results/example_white_bg.png (白色背景)")
    print("  - .results/example_gray_bg.png (灰色背景)")

    # 分析关键像素
    print("\n🔍 关键像素分析:")

    # 左侧低alpha区域 (x=10, alpha≈25)
    left_low_alpha_black = black_bg[50, 10]
    left_low_alpha_white = white_bg[50, 10]
    print(f"左侧低透明度区域:")
    print(f"  黑色背景: {left_low_alpha_black} (应该很暗)")
    print(f"  白色背景: {left_low_alpha_white} (应该很亮)")

    # 右侧50%透明度区域 (x=150, alpha=128)
    right_50_alpha_black = black_bg[50, 150]
    right_50_alpha_white = white_bg[50, 150]
    print(f"右侧50%透明度区域:")
    print(f"  黑色背景: {right_50_alpha_black} (蓝色+黑色混合)")
    print(f"  白色背景: {right_50_alpha_white} (蓝色+白色混合)")

    # 结论
    print(f"\n💡 对于轮胎花纹场景的建议:")
    print(f"  由于轮胎背景是黑色的，推荐使用黑色背景进行转换")
    print(f"  这样可以保持装饰在轮胎上的真实视觉效果")

if __name__ == "__main__":
    main()