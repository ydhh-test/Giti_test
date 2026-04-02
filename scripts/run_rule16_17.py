#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rule 16/17 独立运行脚本

功能:
  从 split/center_horz 和 split/side_horz 读取 RIB 长条图，
  按连续性配置调用拼接算法，输出带主沟的完整胎面图。

调用方式:
    python scripts/run_rule16_17.py --task_id <task_id> [options]

示例:
    # 默认配置（无连续性）
    python scripts/run_rule16_17.py --task_id abc123

    # 指定中间三 RIB 连续
    python scripts/run_rule16_17.py --task_id abc123 --continuity_mode RIB2-RIB3-RIB4

    # 指定边缘连续性概率
    python scripts/run_rule16_17.py --task_id abc123 \\
        --continuity_mode RIB2-RIB3 \\
        --edge_rib12 0.8 \\
        --edge_rib45 0.5

    # 自定义物理参数
    python scripts/run_rule16_17.py --task_id abc123 \\
        --groove_width_mm 12.0 \\
        --pixel_per_mm 3.0 \\
        --blend_width 15
"""

import argparse
import json
import sys
from pathlib import Path

# 保证从项目根目录导入
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from rules.rule16_17 import process_rib_continuity


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Rule 16/17 RIB 横向连续性拼接独立脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--task_id",
        type=str,
        required=True,
        help="任务 ID",
    )
    parser.add_argument(
        "--base_path",
        type=str,
        default=".results",
        help="基础结果路径（默认: .results）",
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="split",
        help="split 子目录名（默认: split）",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="rule16_17",
        help="输出子目录名（默认: rule16_17）",
    )
    parser.add_argument(
        "--continuity_mode",
        type=str,
        default="none",
        choices=["none", "RIB2-RIB3", "RIB3-RIB4", "RIB2-RIB3-RIB4"],
        help="中间 RIB 连续性模式（默认: none）",
    )
    parser.add_argument(
        "--groove_width_mm",
        type=float,
        default=10.0,
        help="主沟宽度，单位 mm（默认: 10.0）",
    )
    parser.add_argument(
        "--pixel_per_mm",
        type=float,
        default=2.0,
        help="像素/毫米比例（默认: 2.0）",
    )
    parser.add_argument(
        "--blend_width",
        type=int,
        default=10,
        help="边缘融合宽度，单位像素（默认: 10）",
    )
    parser.add_argument(
        "--edge_rib12",
        type=float,
        default=None,
        metavar="PROB",
        help="RIB1-RIB2 边缘连续概率 0.0~1.0（默认: 不控制）",
    )
    parser.add_argument(
        "--edge_rib45",
        type=float,
        default=None,
        metavar="PROB",
        help="RIB4-RIB5 边缘连续概率 0.0~1.0（默认: 不控制）",
    )
    parser.add_argument(
        "--group_filter",
        type=str,
        nargs="*",
        default=None,
        metavar="GROUP",
        help="只处理指定分组（可传多个，默认处理全部）",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="以缩进格式打印 JSON 结果",
    )
    return parser.parse_args()


def _validate_prob(value: float, name: str) -> None:
    """校验概率值合法性"""
    if value is not None and not (0.0 <= value <= 1.0):
        raise ValueError(f"{name} 必须在 0.0~1.0 之间，实际值: {value}")


def main() -> None:
    args = parse_args()

    # 参数校验
    _validate_prob(args.edge_rib12, "--edge_rib12")
    _validate_prob(args.edge_rib45, "--edge_rib45")

    # 构造配置字典
    conf = {
        "base_path": args.base_path,
        "input_dir": args.input_dir,
        "output_dir": args.output_dir,
        "continuity_mode": args.continuity_mode,
        "groove_width_mm": args.groove_width_mm,
        "pixel_per_mm": args.pixel_per_mm,
        "blend_width": args.blend_width,
        "group_filter": args.group_filter,
    }

    # 仅在用户明确指定时才写入边缘连续性配置
    edge_continuity: dict = {}
    if args.edge_rib12 is not None:
        edge_continuity["RIB1-RIB2"] = args.edge_rib12
    if args.edge_rib45 is not None:
        edge_continuity["RIB4-RIB5"] = args.edge_rib45
    if edge_continuity:
        conf["edge_continuity"] = edge_continuity

    # 调用 rule16_17
    success, result = process_rib_continuity(args.task_id, conf)

    # 输出 JSON 结果
    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent, default=str))

    if not success:
        sys.exit(1)

    # 打印摘要
    dirs = result.get("directories", {})
    for dir_name, stats in dirs.items():
        total = stats.get("total_count", 0)
        success_count = stats.get("success_count", 0)
        failed_count = stats.get("failed_count", 0)
        skipped_count = stats.get("skipped_count", 0)
        print(
            f"\n[{dir_name}] 合计: {total}  成功: {success_count}"
            f"  失败: {failed_count}  跳过: {skipped_count}"
        )

    output_dir = result.get("output_dir", "")
    if output_dir:
        print(f"\n输出目录: {output_dir}")


if __name__ == "__main__":
    main()
