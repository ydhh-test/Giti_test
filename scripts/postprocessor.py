#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后处理独立脚本

用于开发调试时手动执行完整的后处理流程（所有 9 个阶段）。
调用 postprocessor 中的 postprocessor 函数。

使用方法:
    source .setup_giti_speckit_py12.sh
    python scripts/postprocessor.py --task-id <task_id> [--config <config.json>] [--log <info|debug>]

示例:
    python scripts/postprocessor.py --task-id test_rule6_1
    python scripts/postprocessor.py --task-id test_rule6_1 --config config.json
    python scripts/postprocessor.py --task-id test_rule6_1 --log info
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Union

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.postprocessor import postprocessor
from utils.logger import get_logger

logger = get_logger("postprocessor_script")


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="后处理独立脚本 - 执行完整的后处理流程"
    )
    parser.add_argument(
        "--task-id",
        type=str,
        required=True,
        help="任务唯一标识 (如：9f8d7b6a-5e4d-3c2b-1a09-876543210fed)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="用户配置文件路径 (JSON 格式)，不传则使用空字典"
    )
    parser.add_argument(
        "--log",
        type=str,
        choices=["info", "debug"],
        default="debug",
        help="日志级别：info 或 debug (默认：debug)"
    )
    return parser.parse_args()


def load_user_config(config_path: str) -> Union[dict, str]:
    """
    加载用户配置

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典或文件路径
    """
    if config_path is None:
        return {}

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在：{config_path}")

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """主函数"""
    args = parse_args()
    task_id = args.task_id

    # 设置日志级别
    log_level = args.log.upper()

    # 打印开始信息
    print("=" * 60)
    print("后处理开始")
    print(f"Task ID: {task_id}")
    print(f"日志级别：{log_level}")
    print("=" * 60)

    # 加载用户配置
    try:
        user_conf = load_user_config(args.config)
        if args.config:
            print(f"配置文件：{args.config}")
        else:
            print("用户配置：空字典 (使用默认配置)")
    except Exception as e:
        print(f"\n错误：加载配置文件失败 - {str(e)}")
        print("=" * 60)
        sys.exit(1)

    # 执行后处理
    flag, details = postprocessor(task_id, user_conf)

    # 处理结果
    if flag:
        print("\n" + "=" * 60)
        print("后处理完成")
        print("=" * 60)

        # 打印摘要信息
        # image_gen_number = details.get("image_gen_number", 0)
        # print(f"\n生成图片数：{image_gen_number}")

        # 打印每张图片的信息
        for key in details:
            if key.isdigit():  # 图片信息键：0, 1, 2, ...
                img_info = details[key]
                print(f"\n图片 {key}:")
                print(f"  路径：{img_info.get('image_path', 'N/A')}")
                print(f"  得分：{img_info.get('image_score', 'N/A')}")

        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("后处理失败")
        print("=" * 60)
        print(f"\n错误：{details.get('err_msg', '未知错误')}")
        print(f"失败阶段：{details.get('failed_stage', 'unknown')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
