# -*- coding: utf-8 -*-
"""
rule6_2: 纵图拼接中间层

功能:
- 接收 postprocessor 的调用
- 循环 filter 目录中的所有图片
- 调用 stitch_and_resize() 进行处理
- 保存结果到输出目录

目录关系:
- 输入：.results/task_id_{task_id}/{filter_dir}/
- 输出：.results/task_id_{task_id}/{base_type}_vertical/
  (center_filter → center_vertical, side_filter → side_vertical)

注意:
- 本模块只负责遍历 conf.filters 列表，不关心列表来源
- 配置校验和 filters 构建在 postprocessor.py 中完成
"""

from pathlib import Path
from typing import Dict, List, Tuple, Any
from PIL import Image
import os

from algorithms.stitching.vertical_stitch import stitch_and_resize
from utils.logger import get_logger

logger = get_logger("rule6_2")


# ========== 主入口函数 ==========

def process_vertical_stitch(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    纵图拼接主入口

    参数:
        task_id: 任务 ID
        conf: 配置字典
            - base_path: 基础路径（默认 ".results"）
            - filters: filter 配置列表（由 postprocessor.py 构建）
                - dir: 目录名（如 "center_filter"）
                - stitch_count: 拼接次数
                - resolution: 目标分辨率 [width, height]
            - output_dir_suffix: 输出目录后缀（默认 "_vertical"）

    返回:
        (True, {"task_id": ..., "directories": {...}, "summary": {...}})
        或 (False, {"err_msg": ..., "task_id": ...})
    """
    # Step 1: 配置校验
    filters = conf.get("filters", [])

    if not filters:
        err_msg = "纵图拼接配置错误：filters 不能为空"
        logger.error(err_msg)
        return False, {
            "err_msg": err_msg,
            "task_id": task_id
        }

    # Step 2: 获取基础路径（默认 ".results"）
    base_path = conf.get("base_path", ".results")

    # Step 3: 构建任务目录
    task_dir = Path(base_path) / f"task_id_{task_id}"

    # Step 4: 循环处理每个 filter 目录
    dir_stats = {}
    for filter_config in filters:
        filter_dir = filter_config.get("dir")
        if not filter_dir:
            logger.warning(f"filter_config 缺少 dir 字段，跳过：{filter_config}")
            continue

        # 获取该 filter 的配置参数
        stitch_count = filter_config.get("stitch_count")
        resolution = filter_config.get("resolution")

        if stitch_count is None or resolution is None:
            err_msg = f"filter_config 缺少必需字段 (stitch_count, resolution): {filter_config}"
            logger.error(err_msg)
            # 这个 filter 配置无效，但继续处理其他 filter
            dir_stats[filter_dir] = {
                "total_count": 0,
                "processed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "images": {},
                "err_msg": err_msg
            }
            continue

        resolution = tuple(resolution)

        # 构建输入输出路径
        input_dir = task_dir / filter_dir

        # 输出目录命名：center_filter → center_vertical
        base_type = filter_dir.replace('_filter', '')
        output_dir_suffix = conf.get("output_dir_suffix", "_vertical")
        output_dir = task_dir / f"{base_type}{output_dir_suffix}"

        # 检查输入目录是否存在
        if not input_dir.exists():
            logger.warning(f"输入目录不存在，跳过：{input_dir}")
            dir_stats[filter_dir] = {
                "total_count": 0,
                "processed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "images": {}
            }
            continue

        # 调用单目录处理函数
        flag, stats = process_single_dir(
            input_dir=input_dir,
            output_dir=output_dir,
            stitch_count=stitch_count,
            target_size=resolution,
            task_id=task_id,
            filter_dir=filter_dir
        )

        if not flag:
            # 单目录失败，记录错误但继续处理其他目录
            logger.error(f"处理目录 {filter_dir} 失败：{stats.get('err_msg', '未知错误')}")
            dir_stats[filter_dir] = {
                "total_count": 0,
                "processed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "images": {},
                "err_msg": stats.get("err_msg", "未知错误")
            }
            continue

        dir_stats[filter_dir] = stats

    # Step 5: 聚合统计
    summary = _aggregate_summary(dir_stats)

    return True, {
        "task_id": task_id,
        "directories": dir_stats,
        "summary": summary
    }


def process_single_dir(
    input_dir: Path,
    output_dir: Path,
    stitch_count: int,
    target_size: tuple,
    task_id: str,
    filter_dir: str
) -> Tuple[bool, dict]:
    """
    处理单个 filter 目录

    参数:
        input_dir: 输入目录
        output_dir: 输出目录
        stitch_count: 拼接次数
        target_size: 目标尺寸 (width, height)
        task_id: 任务 ID
        filter_dir: 目录名

    返回:
        (True, 统计字典) 或 (False, {"err_msg": ...})
    """
    try:
        # Step 1: 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"开始处理目录 {filter_dir}, 输出到 {output_dir}")

        # Step 2: 获取图片列表
        image_files = _get_image_files(input_dir)

        if not image_files:
            logger.warning(f"输入目录为空：{input_dir}")
            return True, {
                "total_count": 0,
                "processed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "images": {}
            }

        # Step 3: 统计信息
        stats = {
            "total_count": len(image_files),
            "processed_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "images": {}
        }

        # Step 4: 循环处理每张图片
        for image_path in image_files:
            try:
                # 读取图片
                img = Image.open(image_path)

                # 调用算法函数（输入输出都是 PIL.Image）
                result_img = stitch_and_resize(
                    image=img,
                    stitch_count=stitch_count,
                    target_size=target_size
                )

                # 保存结果
                output_path = output_dir / image_path.name
                result_img.save(output_path, "PNG")

                # 记录成功
                stats["success_count"] += 1
                stats["processed_count"] += 1
                stats["images"][image_path.name] = {
                    "status": "success",
                    "output_path": str(output_path)
                }
                logger.debug(f"成功处理图片：{image_path.name}")

            except Exception as e:
                # 单张图片失败，跳过继续下一张
                stats["failed_count"] += 1
                stats["processed_count"] += 1
                stats["images"][image_path.name] = {
                    "status": "failed",
                    "error": str(e)
                }
                logger.error(f"处理图片失败 {image_path.name}: {str(e)}")

        return True, stats

    except Exception as e:
        # 目录级别错误
        logger.error(f"处理目录 {filter_dir} 时发生错误：{str(e)}")
        return False, {"err_msg": str(e)}


# ========== 辅助函数 ==========

def _get_image_files(dir_path: Path) -> List[Path]:
    """
    获取目录内所有图片文件，按文件名排序
    """
    extensions = ['.png', '.jpg', '.jpeg', '.bmp']
    image_files = []
    for ext in extensions:
        image_files.extend(dir_path.glob(f"*{ext}"))
    return sorted(image_files, key=lambda x: x.name)


def _aggregate_summary(dir_stats: Dict[str, dict]) -> dict:
    """
    聚合各目录统计
    """
    return {
        "total_images": sum(s.get("total_count", 0) for s in dir_stats.values()),
        "total_processed": sum(s.get("processed_count", 0) for s in dir_stats.values()),
        "total_success": sum(s.get("success_count", 0) for s in dir_stats.values()),
        "total_failed": sum(s.get("failed_count", 0) for s in dir_stats.values()),
        "total_skipped": sum(s.get("skipped_count", 0) for s in dir_stats.values())
    }
