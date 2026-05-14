#!/usr/bin/env python3
"""
最终验证：BGRA到BGR转换的正确性
"""

import cv2
import numpy as np
from src.core.operation.image_operation import overlay_decoration, apply_opacity

def main():
    # 创建测试场景
    base_image = np.zeros((100, 500, 3), dtype=np.uint8)
    base_image[:, :, 2] = 200  # 深红色基础

    decoration = np.ones((100, 100, 3), dtype=np.uint8) * 255  # 白色装饰
    decoration_bgra = apply_opacity(decoration, 128)  # 50% 透明度

    print("测试场景:")
    print(f"  基础图像: 深红色 (200)")
    print(f"  装饰图像: 白色 (255) + 50% 透明度")
    print(f"  期望结果: (255 * 0.5) + (200 * 0.5) = 227.5")

    # 应用覆盖
    result = overlay_decoration(base_image, decoration_bgra, decoration_bgra)

    # 检查结果
    left_result = np.mean(result[:, :100, 2])  # 左侧R通道平均值
    expected = 227.5

    print(f"\n实际结果: {left_result:.1f}")
    print(f"期望结果: {expected:.1f}")
    print(f"差异: {abs(left_result - expected):.1f}")

    if abs(left_result - expected) < 2.0:
        print("✅ overlay_decoration 正确实现了视觉不变的3通道输出！")
        return True
    else:
        print("❌ 结果不符合预期")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 结论: 可以实现3通道输出且保持视觉外观不变！")
        print("   推荐在轮胎花纹场景中使用黑色背景假设进行BGRA到BGR转换。")