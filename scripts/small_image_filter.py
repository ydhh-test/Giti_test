#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小图筛选独立脚本

用于开发调试时手动执行后处理流程中的小图筛选阶段（Stage 2）。
调用 postprocessor 中的 _small_image_filter 函数。

使用方法:
    source .setup_giti_speckit_py12.sh
    python scripts/small_image_filter.py --task-id <task_id>

示例:
    python scripts/small_image_filter.py --task-id test_rule6_1
"""

import argparse
import sys
from pathlib import Path

from services.postprocessor import (
    _merge_conf_from_complete_config,
    _small_image_filter,
)
from utils.logger import get_logger

logger = get_logger("small_image_filter")


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="小图筛选独立脚本 - 执行图案连续性检测"
    )
    parser.add_argument(
        "--task-id",
        type=str,
        required=True,
        help="任务唯一标识 (如：9f8d7b6a-5e4d-3c2b-1a09-876543210fed)"
    )
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    task_id = args.task_id

    # 打印开始信息
    print("=" * 50)
    print("小图筛选开始")
    print(f"Task ID: {task_id}")
    print("=" * 50)

    # Stage 1: Conf 处理（复用 postprocessor 逻辑）
    user_conf = {}  # 空字典
    merged_conf = _merge_conf_from_complete_config(task_id, user_conf)
    small_image_filter_conf = merged_conf.get("small_image_filter_conf", {})

    # Stage 2: 执行小图筛选
    flag, details = _small_image_filter(task_id, small_image_filter_conf)

    # 处理结果
    if flag:
        # 成功：打印摘要
        summary = details.get("pattern_continuity_stats", {}).get("summary", {})
        print(f"\n处理结果:")
        print(f"  总图片数：{summary.get('total_images', 0)}")
        print(f"  保留图片数：{summary.get('total_kept', 0)}")
        print(f"  删除图片数：{summary.get('total_deleted', 0)}")

        # 打印保留的文件
        print(f"\n保留文件:")
        for dir_name, stats in details.get("pattern_continuity_stats", {}).get("directories", {}).items():
            filter_dir = Path(".results") / f"task_id_{task_id}" / dir_name
            remaining = [f.name for f in filter_dir.glob("*.png")]
            if remaining:
                print(f"  {dir_name}: {remaining}")

        print("\n" + "=" * 50)
        print("小图筛选完成")
        print("=" * 50)
        sys.exit(0)
    else:
        # 失败：打印错误
        print(f"\n错误：{details.get('err_msg', '未知错误')}")
        print(f"失败阶段：{details.get('failed_stage', 'unknown')}")
        print("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    main()
