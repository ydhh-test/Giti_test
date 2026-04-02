#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rule 16/17 独立运行脚本

功能:
  从 split/center_horz 和 split/side_horz 读取 RIB 长条图，
  按连续性配置调用拼接算法，输出带主沟的完整胎面图。

调用方式:
    python scripts/run_rule16_17.py --task_id <task_id> [--conf_path <path>]

示例:
    # 使用默认配置
    python scripts/run_rule16_17.py --task_id abc123

    # 使用自定义配置文件
    python scripts/run_rule16_17.py --task_id abc123 --conf_path my_conf.json

    # 格式化 JSON 输出
    python scripts/run_rule16_17.py --task_id abc123 --pretty

配置文件说明 (JSON):
    {
      "base_path":        ".results",        // 基础结果路径
      "input_dir":        "split",           // split 子目录名
      "output_dir":       "rule16_17",       // 输出子目录名
      "continuity_mode":  "none",            // none | RIB2-RIB3 | RIB3-RIB4 | RIB2-RIB3-RIB4
      "groove_width_mm":  10.0,              // 主沟宽度 (mm)
      "pixel_per_mm":     2.0,              // 像素/毫米比例
      "blend_width":      10,                // 边缘融合宽度 (像素)
      "edge_continuity": {                   // 边缘连续性概率，可省略
        "RIB1-RIB2": 0.8,
        "RIB4-RIB5": 0.5
      },
      "group_filter":     null               // null 表示处理全部分组
    }
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

_DEFAULT_CONF_PATH = _PROJECT_ROOT / "configs" / "rule16_17_default.json"


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
        "--conf_path",
        type=str,
        default=str(_DEFAULT_CONF_PATH),
        help=f"配置文件路径（JSON，默认: configs/rule16_17_default.json）",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="以缩进格式打印 JSON 结果",
    )
    return parser.parse_args()


def _validate_conf(conf: dict) -> None:
    """校验配置文件中概率值的合法性"""
    for key, value in conf.get("edge_continuity", {}).items():
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"edge_continuity.{key} 必须在 0.0~1.0 之间，实际值: {value}")


def main() -> None:
    args = parse_args()

    # 读取配置文件
    conf_path = Path(args.conf_path)
    if not conf_path.exists():
        print(f"错误: 配置文件不存在: {conf_path}", file=sys.stderr)
        sys.exit(1)
    with conf_path.open("r", encoding="utf-8") as f:
        conf = json.load(f)

    # 校验配置
    _validate_conf(conf)

    # 调用 rule16_17
    success, result = process_rib_continuity(args.task_id, conf)

    # 输出 JSON 结果
    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent, default=str))

    if not success:
        sys.exit(1)

    # 打印摘要到 stderr，保证 stdout 是纯 JSON
    dirs = result.get("directories", {})
    for dir_name, stats in dirs.items():
        total = stats.get("total_count", 0)
        success_count = stats.get("success_count", 0)
        failed_count = stats.get("failed_count", 0)
        skipped_count = stats.get("skipped_count", 0)
        print(
            f"\n[{dir_name}] 合计: {total}  成功: {success_count}"
            f"  失败: {failed_count}  跳过: {skipped_count}",
            file=sys.stderr,
        )

    output_dir = result.get("output_dir", "")
    if output_dir:
        print(f"\n输出目录: {output_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
