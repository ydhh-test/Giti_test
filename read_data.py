# read_data.py
import os
import cv2
from typing import List, Tuple


IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")


def list_images(input_path: str) -> List[str]:
    """
    支持：
    - 输入一个文件夹：返回所有图片路径
    - 输入一个图片文件：返回单个图片路径
    """
    if os.path.isfile(input_path):
        return [input_path]

    if not os.path.isdir(input_path):
        raise FileNotFoundError(f"input_path 不存在: {input_path}")

    files = []
    for name in os.listdir(input_path):
        if name.lower().endswith(IMG_EXTS):
            files.append(os.path.join(input_path, name))

    files.sort()
    return files


def read_image_bgr(img_path: str) -> Tuple[str, any]:
    """
    读取图片，返回 (文件名, BGR图像)
    """
    img = cv2.imread(img_path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"无法读取图片: {img_path}")
    return os.path.basename(img_path), img
