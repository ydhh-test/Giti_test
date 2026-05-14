#!/usr/bin/env python3
"""
测试不同的BGRA到BGR转换方法
"""

import cv2
import numpy as np

def bgra_to_bgr_white_background(bgra_image):
    """将BGRA转换为BGR，假设白色背景"""
    if len(bgra_image.shape) == 3 and bgra_image.shape[2] == 4:
        b, g, r, a = cv2.split(bgra_image.astype(np.float32))
        alpha = a / 255.0

        # 白色背景: (255, 255, 255)
        b_result = b * alpha + 255 * (1 - alpha)
        g_result = g * alpha + 255 * (1 - alpha)
        r_result = r * alpha + 255 * (1 - alpha)

        return cv2.merge([b_result, g_result, r_result]).astype(np.uint8)
    else:
        return bgra_image

def bgra_to_bgr_black_background(bgra_image):
    """将BGRA转换为BGR，假设黑色背景"""
    if len(bgra_image.shape) == 3 and bgra_image.shape[2] == 4:
        b, g, r, a = cv2.split(bgra_image.astype(np.float32))
        alpha = a / 255.0

        # 黑色背景: (0, 0, 0)
        b_result = b * alpha
        g_result = g * alpha
        r_result = r * alpha

        return cv2.merge([b_result, g_result, r_result]).astype(np.uint8)
    else:
        return bgra_image

def bgra_to_bgr_custom_background(bgra_image, background_bgr=(128, 128, 128)):
    """将BGRA转换为BGR，使用自定义背景色"""
    if len(bgra_image.shape) == 3 and bgra_image.shape[2] == 4:
        b, g, r, a = cv2.split(bgra_image.astype(np.float32))
        alpha = a / 255.0

        bg_b, bg_g, bg_r = background_bgr

        b_result = b * alpha + bg_b * (1 - alpha)
        g_result = g * alpha + bg_g * (1 - alpha)
        r_result = r * alpha + bg_r * (1 - alpha)

        return cv2.merge([b_result, g_result, r_result]).astype(np.uint8)
    else:
        return bgra_image

def create_test_image():
    """创建测试图像"""
    # 创建一个渐变alpha通道的图像
    height, width = 200, 400
    test_image = np.zeros((height, width, 4), dtype=np.uint8)

    # 设置RGB为红色
    test_image[:, :, 2] = 255  # BGR中的R通道

    # 创建从左到右的alpha渐变：0 -> 255
    for x in range(width):
        alpha_value = int(255 * x / width)
        test_image[:, x, 3] = alpha_value

    return test_image

def main():
    # 创建测试图像
    test_bgra = create_test_image()
    print(f"原始BGRA图像: {test_bgra.shape}")

    # 应用不同的转换方法
    white_bg = bgra_to_bgr_white_background(test_bgra)
    black_bg = bgra_to_bgr_black_background(test_bgra)
    gray_bg = bgra_to_bgr_custom_background(test_bgra, (128, 128, 128))

    # 保存结果
    cv2.imwrite('.results/bgra_original.png', test_bgra)
    cv2.imwrite('.results/bgra_white_bg.png', white_bg)
    cv2.imwrite('.results/bgra_black_bg.png', black_bg)
    cv2.imwrite('.results/bgra_gray_bg.png', gray_bg)

    print("✅ 测试图像已生成:")
    print("  - .results/bgra_original.png (带alpha通道)")
    print("  - .results/bgra_white_bg.png (白色背景)")
    print("  - .results/bgra_black_bg.png (黑色背景)")
    print("  - .results/bgra_gray_bg.png (灰色背景)")

    # 验证转换结果
    left_pixel = white_bg[100, 10]  # 左侧，alpha接近0
    right_pixel = white_bg[100, 390]  # 右侧，alpha接近255

    print(f"\n白色背景转换结果:")
    print(f"  左侧像素 (低alpha): {left_pixel}")  # 应该接近白色 [255, 255, 255]
    print(f"  右侧像素 (高alpha): {right_pixel}")  # 应该接近红色 [0, 0, 255]

    left_pixel_black = black_bg[100, 10]
    right_pixel_black = black_bg[100, 390]

    print(f"\n黑色背景转换结果:")
    print(f"  左侧像素 (低alpha): {left_pixel_black}")  # 应该接近黑色 [0, 0, 0]
    print(f"  右侧像素 (高alpha): {right_pixel_black}")  # 应该接近红色 [0, 0, 255]

if __name__ == "__main__":
    main()