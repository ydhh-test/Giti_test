# -*- coding: utf-8 -*-

"""
日志模块

提供标准化的日志系统。
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "giti_tire",
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    设置并返回一个配置好的日志记录器。

    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径（可选）
        console_output: 是否输出到控制台

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "giti_tire") -> logging.Logger:
    """
    获取或创建日志记录器。

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器实例
    """
    if not hasattr(logging.Logger, 'manager'):
        return setup_logger(name)

    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


class LoggerMixin:
    """日志记录器混入类，为类提供日志功能。"""

    @property
    def logger(self) -> logging.Logger:
        """获取当前类的日志记录器。"""
        return get_logger(self.__class__.__name__)


# 创建默认日志记录器
default_logger = get_logger("giti_tire")
