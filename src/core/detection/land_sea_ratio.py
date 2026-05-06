"""
海陆比特征计算模块（核心算法层）

功能:
- 计算轮胎花纹的海陆比 (黑色+灰色区域占比)
- 仅返回原始特征值，不含评分逻辑

评分逻辑由 src.rules.scores.rule_13 负责。
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Any


def compute_land_sea_ratio(img: np.ndarray) -> Tuple[float, Dict[str, Any]]:
    """
    计算轮胎花纹样稿的海陆比（纯特征计算，无评分逻辑）。

    Parameters
    ----------
    img : np.ndarray
        输入图片（OpenCV BGR 或灰度 numpy array）。

    Returns
    -------
    ratio_percent : float
        海陆比百分比，如 30.5 表示 30.5%。
    details : dict
        ratio_percent / black_area / gray_area / total_area。
    """
    # 1. 计算图片总面积 (像素总数)
    total_area = img.shape[0] * img.shape[1]

    # 2. 调用子函数计算黑色和灰色区域面积
    black_area = compute_black_area(img)
    gray_area = compute_gray_area(img)

    # 3. 计算海陆比并转换为百分比形式 (例如 30.5 表示 30.5%)
    if total_area == 0:
        ratio_percent = 0.0
    else:
        ratio_percent = ((black_area + gray_area) / total_area) * 100

    # 4. 封装详情（仅特征，无评分；评分由 rules/scores/rule_13.py 负责）
    details = {
        "ratio_percent": round(ratio_percent, 2),
        "black_area":    black_area,
        "gray_area":     gray_area,
        "total_area":    total_area,
    }
    return ratio_percent, details


def compute_black_area(img: np.ndarray, *args, **kwargs) -> int:
    """
    函数作用：计算黑色区域面积
    核心逻辑：将输入图像统一转为单通道灰度图，使用 cv2.inRange 函数设定极暗/黑色的阈值范围 [0, 50]，
             对图像进行二值化掩码（Mask）提取。该掩码中白色代表黑像素，黑色代表背景。
             最后通过 cv2.countNonZero 统计掩码矩阵中的非零像素点总数，即为黑色区域的总像素面积。
    """
    # 转换为灰度图以进行像素强度过滤
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # 使用 cv2.inRange 提取黑色像素。
    black_mask = cv2.inRange(gray, 0, 50)
    black_area = cv2.countNonZero(black_mask)

    return black_area


def compute_gray_area(img: np.ndarray, *args, **kwargs) -> int:
    """
    函数作用：计算灰色区域面积
    核心逻辑：将输入图像统一转为单通道灰度图，使用 cv2.inRange 函数设定灰色过渡区域的阈值范围 [51, 200]，
             提取出所有落在该亮度范围内的像素点并生成掩码（Mask）。
             随后统计该掩码矩阵中非零（有效）像素点的数量，即得出灰色区域所占的绝对像素面积。
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # 提取灰色像素。
    gray_mask = cv2.inRange(gray, 51, 200)
    gray_area = cv2.countNonZero(gray_mask)

    return gray_area
