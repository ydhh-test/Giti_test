# -*- coding: utf-8 -*-
"""
rule6_1: 图案连续性检测中间层

功能:
- 接收 postprocessor 的调用
- 循环 filter 目录中的所有图片
- 调用 detect_pattern_continuity() 进行图案连续性检测
- 删除不连续的图片
- 保存可视化结果

目录关系:
- 输入：.results/task_id_{task_id}/{filter_dir}/
- 可视化输出：.results/task_id_{task_id}/rule6_1/{base_type}/
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple
import shutil
import os
import cv2

from utils.logger import get_logger

logger = get_logger("rule6_1")


def process_pattern_continuity(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    图案连续性检测主入口

    参数:
        task_id: 任务 ID
        conf: 配置字典
            - filter_output_dirs: filter 目录列表 (可选)
            - pattern_continuity_conf: 算法配置
            - visualize: 是否生成可视化
            - output_base_dir: 输出基础目录

    返回:
        (True, 详细统计字典) 或 (False, 错误信息)
    """
    from configs.base_config import SystemConfig

    # 获取 filter 目录列表
    system_config = SystemConfig()
    filter_output_dirs = conf.get(
        'filter_output_dirs',
        system_config.filter_output_dirs
    )

    # 构建基础路径
    base_path = Path(".results") / f"task_id_{task_id}"

    # 按目录循环处理
    dir_stats = {}
    for filter_dir in filter_output_dirs:
        dir_path = base_path / filter_dir

        # 检查目录是否存在
        if not dir_path.exists():
            logger.warning(f"目录不存在，跳过：{dir_path}")
            dir_stats[filter_dir] = {
                "total_count": 0,
                "kept_count": 0,
                "deleted_count": 0,
                "total_score": 0,
                "images": {}
            }
            continue

        # 调用单目录处理函数
        flag, stats = process_pattern_continuity_single_dir(
            dir_path=dir_path,
            filter_dir=filter_dir,
            task_id=task_id,
            conf=conf
        )

        if not flag:
            return False, {
                "err_msg": f"处理目录 {filter_dir} 失败：{stats.get('err_msg', '未知错误')}",
                "task_id": task_id
            }

        dir_stats[filter_dir] = stats

    # 聚合统计
    summary = _aggregate_summary(dir_stats)

    return True, {
        "task_id": task_id,
        "directories": dir_stats,
        "summary": summary
    }


def process_pattern_continuity_single_dir(
    dir_path: Path,
    filter_dir: str,
    task_id: str,
    conf: dict
) -> Tuple[bool, dict]:
    """
    对单个 filter 目录进行图案连续性检测

    参数:
        dir_path: 目录路径
        filter_dir: 目录名 (如 "center_filter")
        task_id: 任务 ID
        conf: 配置字典

    返回:
        (True, 单目录统计) 或 (False, 错误信息)
    """
    from algorithms.detection.pattern_continuity import detect_pattern_continuity

    # 获取图片列表
    image_files = _get_image_files(dir_path)

    # 获取配置
    pattern_continuity_conf = conf.get('pattern_continuity_conf', {})
    visualize = conf.get('visualize', True)

    # 构建可视化输出目录
    # .results/task_id_{task_id}/rule6_1/center/ (center_filter → center)
    vis_output_dir = _build_vis_output_dir(task_id, filter_dir)
    if visualize:
        vis_output_dir.mkdir(parents=True, exist_ok=True)

    # 统计信息
    stats = {
        "total_count": len(image_files),
        "kept_count": 0,
        "deleted_count": 0,
        "total_score": 0,
        "images": {}
    }

    # 循环处理每张图片
    for image_id, image_path in enumerate(image_files):
        try:
            # 读取图片
            img = cv2.imread(str(image_path))
            if img is None:
                logger.warning(f"图片读取失败：{image_path}")
                stats["images"][image_path.name] = {
                    "error": "读取失败",
                    "deleted": True
                }
                stats["deleted_count"] += 1
                continue

            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 调用算法
            # 传递 vis_output_dir 作为 output_base_dir
            # 算法会保存到：{vis_output_dir}/task_id_{task_id}/{image_type}_mid_results/
            score, details = detect_pattern_continuity(
                image=gray,
                conf=pattern_continuity_conf,
                task_id=task_id,
                image_type=filter_dir,
                image_id=str(image_id),
                visualize=visualize,
                output_base_dir=str(vis_output_dir)
            )

            # 判断连续性
            is_continuous = details.get('is_continuous', False)

            # 记录结果
            stats["images"][image_path.name] = {
                "score": score,
                "is_continuous": is_continuous,
                "image_id": str(image_id)
            }

            if is_continuous:
                # 连续：保留图片
                stats["kept_count"] += 1
                stats["total_score"] += score
                logger.debug(f"图片连续，保留：{image_path.name}, score={score}")
            else:
                # 不连续：删除图片
                os.remove(str(image_path))
                stats["deleted_count"] += 1
                stats["images"][image_path.name]["deleted"] = True
                logger.debug(f"图片不连续，删除：{image_path.name}")

        except Exception as e:
            logger.error(f"处理图片失败 {image_path.name}: {str(e)}")
            stats["images"][image_path.name] = {
                "error": str(e),
                "deleted": True
            }
            stats["deleted_count"] += 1

    return True, stats


# ========== 辅助函数 ==========

def _get_image_files(dir_path: Path) -> List[Path]:
    """获取目录内所有图片文件，按文件名排序"""
    extensions = ['.png', '.jpg', '.jpeg', '.bmp']
    image_files = []
    for ext in extensions:
        image_files.extend(dir_path.glob(f"*{ext}"))
    return sorted(image_files, key=lambda x: x.name)


def _copy_images(src_dir: Path, dst_dir: Path) -> None:
    """复制图片文件"""
    if not src_dir.exists():
        return

    dst_dir.mkdir(parents=True, exist_ok=True)

    for img_file in _get_image_files(src_dir):
        shutil.copy2(str(img_file), str(dst_dir / img_file.name))


def _aggregate_summary(dir_stats: Dict[str, dict]) -> dict:
    """聚合各目录统计"""
    return {
        "total_images": sum(s["total_count"] for s in dir_stats.values()),
        "total_kept": sum(s["kept_count"] for s in dir_stats.values()),
        "total_deleted": sum(s["deleted_count"] for s in dir_stats.values()),
        "total_score": sum(s["total_score"] for s in dir_stats.values())
    }


def _build_vis_output_dir(task_id: str, filter_dir: str) -> Path:
    """
    构建可视化输出目录路径

    .results/task_id_{task_id}/rule6_1/{base_type}/
    base_type = center_filter → center
    """
    base_type = filter_dir.replace('_filter', '')
    return Path(".results") / f"task_id_{task_id}" / "rule6_1" / base_type
