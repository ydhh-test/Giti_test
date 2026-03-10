# -*- coding: utf-8 -*-

"""
预处理模块

负责用户输入数据的预处理工作，包括灰边去除、CMYK颜色空间转换。
输入整图，进行训练图片预处理.
"""

# Copyright © 2026. All rights reserved.

import cv2
import numpy as np
import os
import glob
from PIL import Image
import random
from collections import Counter

from utils.logger import get_logger

# 创建模块级日志记录器
logger = get_logger("services_preprocessor")

# ==================== 工具函数 ====================

def _get_image_files(input_dir, extensions=None):
    """获取输入目录中的所有图片文件"""
    if extensions is None:
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tif', '*.tiff']
    img_files = []
    for ext in extensions:
        img_files.extend(glob.glob(os.path.join(input_dir, ext)))
        img_files.extend(glob.glob(os.path.join(input_dir, ext.upper())))
    return sorted(img_files)  # 排序确保处理顺序一致

def _save_image(image, output_path):
    """统一保存图像，自动处理路径创建"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, image)
    return output_path

def _ensure_dir(dir_path):
    """确保目录存在"""
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

# ==================== 图像处理核心函数 ====================

def remove_black_and_split_segments(image_input, num_segments_to_remove=4):
    """
    删除图像中连续全黑列中宽度最大的num_segments_to_remove段，
    返回剩余连续列段的独立图片列表
    
    Args:
        image_input: 图像路径(str)或numpy数组
        num_segments_to_remove: 要移除的黑色段数量
    
    Returns:
        list: [(img_array, part_name), ...]
    """
    # 统一读取图像
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
        if img is None:
            raise ValueError(f"无法读取图片: {image_input}")
        base_name = os.path.splitext(os.path.basename(image_input))[0]
    else:
        img = image_input.copy()
        base_name = "segment"
    
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, c = img_rgb.shape

    # 检测全黑列
    black_mask = np.all(img_rgb == 0, axis=2).all(axis=0)
    
    # 提取黑色段
    segments = []
    start = None
    for i in range(w):
        if black_mask[i]:
            if start is None:
                start = i
        else:
            if start is not None:
                segments.append((start, i-1))
                start = None
    if start is not None:
        segments.append((start, w-1))

    # 确定要移除的黑色段（最大的num_segments_to_remove个）
    if segments:
        segments_sorted = sorted(segments, key=lambda x: x[1]-x[0]+1, reverse=True)
        segments_to_remove = segments_sorted[:num_segments_to_remove]  # 直接切片，保持为元组列表
    else:
        segments_to_remove = []

    # 提取保留的段
    keep_mask = np.ones(w, dtype=bool)
    for s, e in segments_to_remove:
        keep_mask[s:e+1] = False

    remaining_segments = []
    start = None
    for i in range(w):
        if keep_mask[i]:
            if start is None:
                start = i
        else:
            if start is not None:
                remaining_segments.append((start, i-1))
                start = None
    if start is not None:
        remaining_segments.append((start, w-1))

    # 构建结果
    parts = []
    for idx, (s, e) in enumerate(remaining_segments):
        part_img = img_rgb[:, s:e+1, :]
        parts.append((part_img, f"{base_name}_part{idx+1}"))
    
    return parts

def remove_side_white(image, direction='left'):
    """
    去除图像单侧的白色边缘
    
    Args:
        image: numpy数组 (RGB或BGR)
        direction: 'left' 或 'right'，表示要去除哪一侧的白边
    
    Returns:
        裁剪后的图像
    """
    # 统一转换为灰度图
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    # 二值化检测白色区域
    _, thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
    height, width = thresh.shape[:2]
    
    if direction == 'right':
        # 从右向左查找第一个非白色列
        for col in range(width-1, -1, -1):
            if thresh[:, col].sum() < height * 255:
                return image[:, :col+1]
        return image  # 全是白色，返回原图
    else:
        # 从左向右查找第一个非白色列
        for col in range(width):
            if thresh[:, col].sum() < height * 255:
                return image[:, col:]
        return image  # 全是白色，返回原图


def convert_cmyk_to_rgb(img_pil):
    """
    将PIL CMYK图像转换为OpenCV BGR格式（内存转换，无需文件IO）
    
    Args:
        img_pil: PIL Image对象 (CMYK模式)
    
    Returns:
        numpy数组 (BGR格式)
    """
    # CMYK转RGB使用PIL内置方法，避免文件IO
    img_rgb = img_pil.convert('RGB')
    return cv2.cvtColor(np.array(img_rgb), cv2.COLOR_RGB2BGR)


def analyze_dominant_color(image_input, lower_bound=15, upper_bound=240, default_color=(137,137,137)):
    """
    分析图像主色调，返回在指定范围内的主要颜色
    
    Args:
        image_input: 图像路径或numpy数组
        lower_bound: 颜色下限
        upper_bound: 颜色上限
        default_color: 默认颜色
    
    Returns:
        tuple: (R, G, B)
    """
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
        if img is None:
            return default_color
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    else:
        img_rgb = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB) if image_input.shape[2] == 3 else image_input
    
    pixels = img_rgb.reshape(-1, 3)
    unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
    top_colors = unique_colors[np.argsort(-counts)[:10]]
    
    for color in top_colors:
        if np.all((color >= lower_bound) & (color <= upper_bound)):
            return tuple(color)
    
    return default_color


def remove_edge_gray(image_input, output_path=None, target_gray=(137,137,137), 
                     tolerance=90, edge_percent=23):
    """
    将图片左右边缘的特定灰色背景替换为白色
    
    Args:
        image_input: 图像路径或PIL Image对象
        output_path: 输出路径（可选）
        target_gray: 目标灰色RGB值
        tolerance: 容差
        edge_percent: 边缘宽度百分比
    
    Returns:
        处理后的BGR图像数组
    """
    # 读取图像
    if isinstance(image_input, str):
        img = Image.open(image_input)
        is_cmyk = img.mode == "CMYK"
        if is_cmyk:
            img_cv = convert_cmyk_to_rgb(img)
            img_cv = cv2.cvtColor(255 - img_cv, cv2.COLOR_RGB2BGR)  # 反转颜色
        else:
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    elif isinstance(image_input, Image.Image):
        is_cmyk = image_input.mode == "CMYK"
        if is_cmyk:
            img_cv = convert_cmyk_to_rgb(image_input)
            img_cv = cv2.cvtColor(255 - img_cv, cv2.COLOR_RGB2BGR)
        else:
            img_cv = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
    else:
        img_cv = image_input.copy()
    
    height, width = img_cv.shape[:2]
    result = img_cv.copy()
    
    # 计算边缘宽度
    edge_width = int(width * edge_percent / 100)
    
    # 灰色范围
    target = np.array(target_gray)
    lower_bound = np.clip(target - tolerance, 0, 255)
    upper_bound = np.clip(target + tolerance, 0, 255)
    
    # 处理左边缘
    left_edge = result[:, :edge_width]
    mask_left = np.all((left_edge > lower_bound) & (left_edge < upper_bound), axis=2)
    left_edge[mask_left] = [255, 255, 255]
    
    # 处理右边缘
    right_edge = result[:, -edge_width:]
    mask_right = np.all((right_edge > lower_bound) & (right_edge < upper_bound), axis=2)
    right_edge[mask_right] = [255, 255, 255]
    
    # 保存
    if output_path:
        _save_image(result, output_path)
    
    return result


def remove_vertical_lines_center(image, x_tolerance=2, length_ratio=0.7,
                                 line_width=2, margin_ratio=0.1,
                                 hough_threshold=50, min_line_gap=10):
    """
    检测图像中央区域的竖直线并去除，保护与其他线段的交点
    """
    if isinstance(image, str):
        img = cv2.imread(image)
        if img is None:
            raise ValueError(f"无法读取图像: {image}")
    else:
        img = image.copy()

    height, width = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    min_line_length = int(height * length_ratio)
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180,
                           threshold=hough_threshold,
                           minLineLength=min_line_length,
                           maxLineGap=min_line_gap)
    
    if lines is None:
        return None

    # 定义中央区域
    left_bound = int(width * margin_ratio)
    right_bound = int(width * (1 - margin_ratio))
    
    vertical_mask = np.zeros((height, width), dtype=np.uint8)
    other_mask = np.zeros((height, width), dtype=np.uint8)
    
    for line in lines:
        x1, y1, x2, y2 = line[0]
        # 统一方向
        if y1 > y2:
            x1, y1, x2, y2 = x2, y2, x1, y1
        
        is_vertical = abs(x1 - x2) <= x_tolerance
        x_min, x_max = min(x1, x2), max(x1, x2)
        in_center = (x_min >= left_bound) and (x_max <= right_bound)
        
        if is_vertical and in_center:
            cv2.line(vertical_mask, (x1, y1), (x2, y2), 255, line_width)
        else:
            cv2.line(other_mask, (x1, y1), (x2, y2), 255, line_width)
    
    if not np.any(vertical_mask):
        return None
    
    # 计算并保护交点
    intersection = cv2.bitwise_and(vertical_mask, other_mask)
    kernel = np.ones((3,3), np.uint8)
    intersection_dilated = cv2.dilate(intersection, kernel)
    vertical_mask_clean = cv2.bitwise_and(vertical_mask, cv2.bitwise_not(intersection_dilated))
    
    # 应用掩码
    result = img.copy()
    result[vertical_mask_clean > 0] = [255, 255, 255]
    
    return result


def detect_periodic_blocks(image_input, min_cycles=5, max_cycles=7, min_block_pixels=100):
    """
    检测图像中的周期性色块并返回第一个有效周期块
    
    Args:
        image_input: 图像路径或numpy数组
        min_cycles: 最小周期数
        max_cycles: 最大周期数
        min_block_pixels: 最小有效像素数
    
    Returns:
        numpy数组或None
    """
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
        if img is None:
            raise ValueError("无法读取图像")
    else:
        img = image_input.copy()
    
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 二值化
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # 计算垂直密度
    row_density = np.sum(binary, axis=1) / w
    row_density = row_density.astype(np.float32)
    row_density -= np.mean(row_density)
    
    # 自相关分析
    autocorr = np.correlate(row_density, row_density, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    
    # 确定周期范围
    min_period = h // max_cycles
    max_period = h // min_cycles
    peak_threshold = 0.3 * np.max(autocorr)
    
    # 寻找峰值
    peak_lags = []
    for lag in range(min_period, min(max_period, len(autocorr)-1)):
        if (autocorr[lag] > autocorr[lag-1] and 
            autocorr[lag] > autocorr[lag+1] and 
            autocorr[lag] > peak_threshold):
            peak_lags.append(lag)
    
    if not peak_lags:
        return None
    
    period = int(np.median(peak_lags))
    cycle_count = h // period
    
    if not (min_cycles <= cycle_count <= max_cycles):
        logger.debug(f"周期数{cycle_count}不在范围内[{min_cycles}-{max_cycles}]")
        return None
    
    # 返回第一个有效周期块
    for i in range(cycle_count):
        start_y = i * period
        end_y = min((i + 1) * period, h)
        cycle_block = img[start_y:end_y, :, :]
        
        # 验证有效性
        cycle_gray = cv2.cvtColor(cycle_block, cv2.COLOR_BGR2GRAY)
        _, cycle_binary = cv2.threshold(cycle_gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        if np.sum(cycle_binary) > min_block_pixels:
            logger.debug(f"找到周期性色块，周期数={cycle_count}")
            return cycle_block
    
    return None


def random_horizontal_crop(image_input, min_splits=5, max_splits=7):
    """
    随机水平裁剪图像的一部分
    
    Args:
        image_input: 图像路径或numpy数组
        min_splits: 最小分割数
        max_splits: 最大分割数
    
    Returns:
        裁剪后的图像块
    """
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
        if img is None:
            raise ValueError(f"无法读取图像: {image_input}")
    else:
        img = image_input.copy()
    
    h, w = img.shape[:2]
    split_count = random.randint(min_splits, max_splits)
    
    base_height = h // split_count
    block_height = base_height + 1
    
    # 随机起始位置
    max_start = max(1, h - block_height)
    current_y = random.randint(0, max_start)
    end_y = min(current_y + block_height, h)
    
    return img[current_y:end_y, :, :]


# ==================== 流程控制函数 ====================

def process_vertical_split(input_dir, center_output_dir, side_output_dir):
    """
    纵向切分主流程：将输入图像按主沟切分为center和side
    
    Args:
        input_dir: 输入图像目录
        center_output_dir: 中间部分输出目录 (center_horz)
        side_output_dir: 两侧部分输出目录 (side_horz_with_gray)
    """
    _ensure_dir(center_output_dir)
    _ensure_dir(side_output_dir)
    
    img_files = _get_image_files(input_dir)
    if not img_files:
        logger.warning(f"输入目录 {input_dir} 中没有找到图片")
        return 0
    
    processed_count = 0
    
    for img_path in img_files:
        logger.debug(f"处理图片: {img_path}")
        
        try:
            vertical_parts = remove_black_and_split_segments(img_path)
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            
            # 处理5个部分：1和5为side，2-4为center
            for idx, (img_part, part_name) in enumerate(vertical_parts, 1):
                part_idx = idx  # 1-based index
                
                # 去除白边
                if part_idx == 1:
                    img_part = remove_side_white(img_part, direction='left')
                elif part_idx == 5:
                    img_part = remove_side_white(img_part, direction='right')
                
                # 转换为BGR并检查尺寸
                part_bgr = cv2.cvtColor(img_part, cv2.COLOR_RGB2BGR)
                height, width = part_bgr.shape[:2]
                
                if width < 5:  # 过滤异常细长条
                    logger.warning(f"跳过过窄的图像段: {part_name}, 宽度={width}")
                    continue
                
                # 保存到对应目录
                output_filename = f"{base_name}_{part_name}_split.png"
                
                if part_idx in [1, 5]:
                    output_path = os.path.join(side_output_dir, output_filename)
                    _save_image(part_bgr, output_path)
                    logger.debug(f"保存侧边: {output_path}")
                else:
                    output_path = os.path.join(center_output_dir, output_filename)
                    _save_image(part_bgr, output_path)
                    logger.debug(f"保存中间: {output_path}")
                
                processed_count += 1
                
        except Exception as e:
            logger.error(f"处理纵向切分失败 {img_path}: {e}")
            raise
    
    return processed_count


def batch_remove_gray_edge(input_dir, output_dir, tolerance=20, edge_percent=50):
    """
    批量去除图像边缘灰色
    
    Args:
        input_dir: 输入目录 (side_horz_with_gray)
        output_dir: 输出目录 (side_horz)
        tolerance: 灰色容差
        edge_percent: 边缘百分比
    """
    _ensure_dir(output_dir)
    
    img_files = _get_image_files(input_dir)
    processed_count = 0
    
    for img_path in img_files:
        try:
            # 分析主色调并去除灰边
            dominant_color = analyze_dominant_color(img_path)
            output_path = os.path.join(output_dir, os.path.basename(img_path))
            
            remove_edge_gray(img_path, output_path, dominant_color, tolerance, edge_percent)
            logger.debug(f"已去灰边: {os.path.basename(img_path)}")
            processed_count += 1
            
        except Exception as e:
            logger.error(f"处理灰边去除失败 {img_path}: {e}")
    
    return processed_count


def process_horizontal_split(input_dir, output_dir, is_side=False):
    """
    横向切分处理：对图像进行周期性检测或随机裁剪
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        is_side: 是否为侧边图像（影响处理参数）
    """
    _ensure_dir(output_dir)
    
    img_files = _get_image_files(input_dir)
    processed_count = 0
    
    for img_path in img_files:
        logger.debug(f"处理横向切分: {img_path}")
        
        try:
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            
            # 尝试周期性检测
            image_part = detect_periodic_blocks(img_path, min_cycles=5, max_cycles=7)
            
            if image_part is None:
                # 使用随机裁剪
                image_part = random_horizontal_crop(img_path, min_splits=5, max_splits=7)
                save_path = os.path.join(output_dir, f"{base_name}_random.png")
                suffix = "random"
            else:
                save_path = os.path.join(output_dir, f"{base_name}_periodic.png")
                suffix = "periodic"
            
            # 保存初步结果
            _save_image(image_part, save_path)
            
            # 去除竖线
            de_line_params = {
                'x_tolerance': 1 if is_side else 2,
                'length_ratio': 0.5 if is_side else 0.7,
                'line_width': 3
            }
            de_line_image = remove_vertical_lines_center(image_part, **de_line_params)
            
            if de_line_image is not None:
                de_line_path = os.path.join(output_dir, f"{base_name}_{suffix}_de_line.png")
                _save_image(de_line_image, de_line_path)
            
            processed_count += 1
            
        except Exception as e:
            logger.error(f"处理横向切分失败 {img_path}: {e}")
            raise
    
    return processed_count

def analyze_image_abnormalities(directory_path):
    """
    分析目录下所有图片的异常情况（优化版）
    """
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
    abnormal_images = []
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if not any(file.lower().endswith(ext) for ext in image_extensions):
                continue
            
            file_path = os.path.join(root, file)
            
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    
                    # 检查尺寸异常
                    abnormalities = []
                    
                    if height > 0 and width / height > 4:
                        abnormalities.append(f"宽高比异常(宽/高={width/height:.2f}>4)")
                    elif width > 0 and height / width > 4:
                        abnormalities.append(f"宽高比异常(高/宽={height/width:.2f}>4)")
                    
                    # 检查颜色异常
                    img_rgb = img.convert('RGB')
                    img_array = np.array(img_rgb)
                    pixels = img_array.reshape(-1, 3)
                    unique_colors = len(set(map(tuple, pixels)))
                    
                    if unique_colors < 3:
                        abnormalities.append(f"颜色种类过少({unique_colors}<3)")
                    
                    if abnormalities:
                        desc = "，".join(abnormalities)
                        abnormal_images.append((file_path, desc, width, height, unique_colors))
                        logger.info(f"异常图片: {file} - {desc}")
                        
            except Exception as e:
                error_info = (file_path, f"处理错误: {str(e)}", 0, 0, 0)
                abnormal_images.append(error_info)
                logger.error(f"无法处理 {file}: {e}")
    
    return abnormal_images


# ==================== 主入口函数 ====================

def tire_image_preprocessing_pipeline(workspace_dir):
    """
    轮胎图像预处理完整流程
    
    流程:
    1. workspace_dir/images -> 读取输入图像
    2. workspace_dir/split/center_horz 和 side_horz_with_gray -> 纵向切分
    3. workspace_dir/split/side_horz -> 去除side的灰边
    4. workspace_dir/pieces/center 和 side -> 横向切分
    5. 异常检测
    
    Args:
        workspace_dir: 工作空间目录路径
    """
    # 定义目录结构
    paths = {
        'input': os.path.join(workspace_dir, "images"),
        'split': os.path.join(workspace_dir, "split"),
        'output': os.path.join(workspace_dir, "pieces"),
        'center_horz': os.path.join(workspace_dir, "split", "center_horz"),
        'side_horz_with_gray': os.path.join(workspace_dir, "split", "side_horz_with_gray"),
        'side_horz': os.path.join(workspace_dir, "split", "side_horz"),
        'center_final': os.path.join(workspace_dir, "pieces", "center"),
        'side_final': os.path.join(workspace_dir, "pieces", "side"),
    }
    
    # 创建所有必要目录
    for dir_path in paths.values():
        _ensure_dir(dir_path)
    
    try:
        # 步骤1: 检查输入
        logger.info(f"开始预处理流程，工作目录: {workspace_dir}")
        img_files = _get_image_files(paths['input'])
        
        if not img_files:
            raise ValueError(f"输入目录 {paths['input']} 中没有找到有效的图片文件")
        
        logger.info(f"找到 {len(img_files)} 个输入文件")
        
        # 步骤2: 纵向切分
        logger.info("步骤2: 执行纵向切分...")
        count = process_vertical_split(
            paths['input'],
            paths['center_horz'],
            paths['side_horz_with_gray']
        )
        logger.info(f"纵向切分完成，处理了 {count} 个图像段")
        
        # 步骤3: 去除灰边（仅处理side）
        logger.info("步骤3: 去除边缘灰边...")
        count = batch_remove_gray_edge(
            paths['side_horz_with_gray'],
            paths['side_horz'],
            tolerance=20,
            edge_percent=50
        )
        logger.info(f"灰边去除完成，处理了 {count} 个文件")
        
        # 步骤4: 横向切分
        logger.info("步骤4: 执行横向切分...")
        
        # 处理side
        count_side = process_horizontal_split(
            paths['side_horz'],
            paths['side_final'],
            is_side=True
        )
        logger.info(f"侧边横向切分完成，处理了 {count_side} 个文件")
        
        # 处理center
        count_center = process_horizontal_split(
            paths['center_horz'],
            paths['center_final'],
            is_side=False
        )
        logger.info(f"中间横向切分完成，处理了 {count_center} 个文件")
        
        # 步骤5: 异常检测，检查pieces目录下的异常图片
        logger.info("步骤5: 执行异常检测...")
        abnormal_images = analyze_image_abnormalities(paths['output'])
        
        if abnormal_images:
            logger.warning(f"发现 {len(abnormal_images)} 个疑似异常图片，请检查:")
            for info in abnormal_images[:5]:  # 只显示前5个
                logger.warning(f"  - {info[0]}: {info[1]}")
        else:
            logger.info("未检测到异常图片")
        
        logger.info("=" * 50)
        logger.info("轮胎图像预处理流程全部完成！")
        logger.info(f"  输入文件: {len(img_files)}")
        # 统计各目录中的文件数量，先检查目录是否存在
        center_horz_count = len(os.listdir(paths['center_horz'])) if os.path.exists(paths['center_horz']) else 0
        side_horz_count = len(os.listdir(paths['side_horz'])) if os.path.exists(paths['side_horz']) else 0
        center_final_count = len(os.listdir(paths['center_final'])) if os.path.exists(paths['center_final']) else 0
        side_final_count = len(os.listdir(paths['side_final'])) if os.path.exists(paths['side_final']) else 0      
        logger.info(f"  中间结果: center_horz={center_horz_count}, "
                   f"side_horz={side_horz_count}")
        logger.info(f"  最终输出: center={center_final_count}, "
                   f"side={side_final_count}")
        
        return {
            'status': 'success',
            'input_count': len(img_files),
            'abnormal_count': len(abnormal_images),
            'abnormal_images': abnormal_images
        }
        
    except Exception as e:
        logger.error(f"预处理流程失败: {str(e)}")
        raise RuntimeError(f"轮胎图像预处理失败: {str(e)}")


if __name__ == "__main__":
    # 测试运行示例
    import sys
    #定义一个工作目录，workspace/input下包含了输入的图片
    workspace = r"./tests/datasets"   
    #tire_image_preprocessing_pipeline(workspace)