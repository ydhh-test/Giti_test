# 几何合理性分析（周期检测、海陆比）

import cv2
import numpy as np


def compute_land_sea_ratio(img, conf: dict, *args, **kwargs):
    """
    函数作用：计算输入轮胎花纹样稿的海陆比，并给出评分
    核心逻辑：
        1. 空间量化：获取图像的宽高尺寸，计算出总像素点数作为轮胎样稿的总面积
        2. 特征提取：调用子函数，利用灰度阈值分割法分别提取代表深沟槽的"黑色区域"和代表浅沟槽/细花的"灰色区域"
        3. 占比计算：将黑、灰区域面积相加，除以总面积并转化为百分比格式
        4. 阶梯评分：将计算出的实际百分比与配置文件传入的标准阈值进行比对，实施三级容差评分
           - 落在目标区间 [target_min, target_max] 内得 2 分（优秀）
           - 落在目标区间外，但在容差边界 (margin) 允许的缓冲范围内得 1 分（及格）
           - 偏离标准范围过大则得 0 分（不合格）

    输入参数：
        img：输入图片 (OpenCV 读取的 numpy array)
        conf：合格指标分数范围（eg：28% - 35% 为通过）、图片黑色面积、图片灰色面积等配置
    返回值：
        score：输入图片海陆比专项评分（2 值评分，即 0, 1, 2）
        details：输入图片的海陆比值、判定指标、黑色面积、灰色面积 (dict 类型)
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

    # 4. 从 conf 读取评分阈值参数
    target_min = conf.get("target_min", 28.0)
    target_max = conf.get("target_max", 35.0)
    margin = conf.get("margin", 5.0)

    # 5. 评分核心逻辑
    if target_min <= ratio_percent <= target_max:
        score = 2
    elif (target_min - margin) <= ratio_percent < target_min or target_max < ratio_percent <= (target_max + margin):
        score = 1
    else:
        score = 0

    # 6. 封装细节数据
    details = {
        "ratio_value": round(ratio_percent, 2),
        "target_range": f"[{target_min}%, {target_max}%]",
        "black_area": black_area,
        "gray_area": gray_area,
        "total_area": total_area
    }

    return score, details


def compute_black_area(img, *args, **kwargs):
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


def compute_gray_area(img, *args, **kwargs):
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
