# -*- coding: utf-8 -*-
"""
rule1to5: 规则 1-5 处理模块

功能:
- 横图拼接中间层
- 接收 postprocessor 的调用
- 调用 HorizontalStitch.process() 进行处理
- 返回与 rule6_2 风格一致的统计信息

目录关系:
- 输入：.results/task_id_{task_id}/center_vertical/
       .results/task_id_{task_id}/side_vertical/
- 输出：.results/task_id_{task_id}/combine_horizontal/
"""

from pathlib import Path
from typing import Dict, Tuple, Any
from algorithms.stitching.horizontal_stitch import HorizontalStitch
from configs.user_config import DEFAULT_HORIZONTAL_STITCH_CONF
from utils.logger import get_logger

logger = get_logger("rule1to5")


def process_horizontal_stitch(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    横图拼接主入口

    参数:
        task_id: 任务 ID
        conf: 配置字典 (扁平配置，已包含 horizontal_stitch 所需所有字段)
            - center_dir: 将被覆盖为 {task_dir}/center_vertical
            - side_dir: 将被覆盖为 {task_dir}/side_vertical
            - output_dir: 将被覆盖为 {task_dir}/combine_horizontal

    返回:
        成功：(True, {
            "task_id": task_id,
            "directories": {
                "combine_horizontal": {
                    "total_count": ...,
                    "processed_count": ...,
                    "success_count": ...,
                    "failed_count": ...,
                    "skipped_count": ...,
                    "images": {
                        "sym_0_*.png": {"status": "success", "output_path": "..."},
                        ...
                    }
                }
            },
            "summary": {...}
        })
        失败：(False, {"err_msg": ..., "task_id": ...})
    """
    try:
        # Step 1: 配置校验
        if not conf:
            err_msg = "横图拼接配置错误：conf 不能为空"
            logger.error(err_msg)
            return False, {"err_msg": err_msg, "task_id": task_id}

        # Step 2: 合并默认配置
        merged_conf = _merge_conf(conf)

        # Step 3: 构建输入输出路径
        base_path = merged_conf.get("base_path", ".results")
        task_dir = Path(base_path) / f"task_id_{task_id}"

        # 覆盖输入输出目录
        merged_conf['center_dir'] = str(task_dir / "center_vertical")
        merged_conf['side_dir'] = str(task_dir / "side_vertical")
        merged_conf['output_dir'] = str(task_dir / "combine_horizontal")

        # 设置 history_file 为当前 task_id 目录下的文件
        merged_conf['history_file'] = str(task_dir / "history_counts.json")

        # Step 4: 调用 HorizontalStitch
        stitcher = HorizontalStitch(task_id, merged_conf)
        flag, result = stitcher.process()

        if not flag:
            err_msg = result.get('error', '横图拼接失败')
            logger.error(f"横图拼接失败：{err_msg}")
            return False, {"err_msg": err_msg, "task_id": task_id}

        # Step 5: 转换为 rule6_2 风格返回
        stats = _build_stats(result)

        return True, {
            "task_id": task_id,
            "directories": {"combine_horizontal": stats},
            "summary": _aggregate_summary(stats)
        }

    except Exception as e:
        logger.error(f"横图拼接异常：{str(e)}")
        return False, {"err_msg": str(e), "task_id": task_id}


def _merge_conf(user_conf: dict) -> dict:
    """合并用户配置与默认配置"""
    return {**DEFAULT_HORIZONTAL_STITCH_CONF, **user_conf}


def _build_stats(result: dict) -> dict:
    """
    将 HorizontalStitch 的返回转换为 rule6_2 风格的 stats 格式
    """
    images_dict = {}
    image_list = result.get('images', [])

    for img_info in image_list:
        filename = img_info.get('filename', 'unknown')
        images_dict[filename] = {
            "status": "success",
            "output_path": img_info.get('output_path', ''),
            "symmetry": img_info.get('symmetry', ''),
            "score": img_info.get('score', 0.0)
        }

    generated_count = len(image_list)

    return {
        "total_count": generated_count,
        "processed_count": generated_count,
        "success_count": generated_count,
        "failed_count": 0,
        "skipped_count": 0,
        "images": images_dict
    }


def _aggregate_summary(stats: dict) -> dict:
    """聚合统计信息（与 rule6_2 风格一致）"""
    return {
        "total_images": stats.get("total_count", 0),
        "total_processed": stats.get("processed_count", 0),
        "total_success": stats.get("success_count", 0),
        "total_failed": stats.get("failed_count", 0),
        "total_skipped": stats.get("skipped_count", 0)
    }
