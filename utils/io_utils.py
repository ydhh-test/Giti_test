"""
I/O工具模块
提供文件读写、路径处理等辅助函数
"""

import os
import json
from typing import List, Optional, Dict, Any


def list_images(directory: str, valid_extensions: tuple = ('.png', '.jpg', '.jpeg', '.bmp', '.tif')) -> List[str]:
    """
    列出目录下的所有图片文件

    Args:
        directory: 目录路径
        valid_extensions: 有效的图片扩展名

    Returns:
        图片文件名列表
    """
    if not os.path.exists(directory):
        return []

    return [f for f in os.listdir(directory) if f.lower().endswith(valid_extensions)]


def ensure_directory(path: str) -> None:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径
    """
    os.makedirs(path, exist_ok=True)


def load_json(file_path: str, default: Any = None) -> Any:
    """
    加载JSON文件

    Args:
        file_path: 文件路径
        default: 默认返回值

    Returns:
        加载的数据，加载失败返回default
    """
    if not os.path.exists(file_path):
        return default

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def save_json(file_path: str, data: Any, ensure_ascii: bool = False, indent: int = 2) -> bool:
    """
    保存数据到JSON文件

    Args:
        file_path: 文件路径
        data: 要保存的数据
        ensure_ascii: 是否转义非ASCII字符
        indent: 缩进空格数

    Returns:
        保存成功返回True，否则返回False
    """
    try:
        ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
        return True
    except Exception:
        return False


def get_file_name_without_ext(file_path: str) -> str:
    """
    获取文件名（不含扩展名）

    Args:
        file_path: 文件路径

    Returns:
        文件名（不含扩展名）
    """
    return os.path.splitext(os.path.basename(file_path))[0]


def get_file_extension(file_path: str) -> str:
    """
    获取文件扩展名

    Args:
        file_path: 文件路径

    Returns:
        文件扩展名（含点号）
    """
    return os.path.splitext(file_path)[1]


def join_path(*paths: str) -> str:
    """
    拼接路径

    Args:
        *paths: 路径组件

    Returns:
        拼接后的路径
    """
    return os.path.join(*paths)
