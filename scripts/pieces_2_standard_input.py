#!/usr/bin/env python3
"""
图片批量处理脚本：将 center 和 side 目录中的 PNG 图片 resize 为 128x128，
并按顺序重命名保存到对应的输出目录。

调用方式:
    python scripts/pieces_2_standard_input.py --task_id <task_id>
"""

import argparse
import shutil
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="将 pieces 目录中的图片 resize 为 128x128 并重新命名"
    )
    parser.add_argument(
        "--task_id",
        type=str,
        required=True,
        help="任务 ID"
    )
    return parser.parse_args()


def process_directory(source_dir: Path, target_dir: Path) -> int:
    """
    处理单个目录下的所有 PNG 图片

    Args:
        source_dir: 源目录路径
        target_dir: 目标目录路径

    Returns:
        成功处理的图片数量
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"源目录不存在：{source_dir}")

    # 清空/创建目标目录
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # 获取所有 PNG 文件，按文件名字典序排序
    png_files = sorted(source_dir.glob("*.png"))

    # 处理每张图片
    for idx, png_file in enumerate(png_files):
        img = Image.open(png_file)
        img_resized = img.resize((128, 128))
        output_path = target_dir / f"{idx}.png"
        img_resized.save(output_path)

    return len(png_files)


def main():
    """主函数"""
    args = parse_args()

    # 构建路径
    base_dir = Path(f".results/task_id_{args.task_id}")
    pieces_dir = base_dir / "pieces"

    source_center = pieces_dir / "center"
    source_side = pieces_dir / "side"
    target_center = base_dir / "center_inf"
    target_side = base_dir / "side_inf"

    # 处理 center 目录
    center_count = process_directory(source_center, target_center)

    # 处理 side 目录
    side_count = process_directory(source_side, target_side)

    # 输出统计信息
    total_count = center_count + side_count
    print(f"Successfully processed {total_count} images (center: {center_count}, side: {side_count})")


if __name__ == "__main__":
    main()
