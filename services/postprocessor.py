# -*- coding: utf-8 -*-

"""
后处理模块

后处理主逻辑包括：
1，小图筛选阶段
2，拼图阶段
3，大图打分阶段
4，输出整理阶段
"""

# Copyright © 2026 云端辉鸿. All rights reserved.
# Author: 桂禹 <guiyu@cloudhuihong.com>
# AI Assistant: ClaudeCode (Claude Sonnet 4)


def postprocessor(task_id: str, conf: dict, user_conf: dict) -> tuple[int, dict]:
    """
    后处理入口函数

    Args:
        task_id: 任务ID
        conf: 配置字典
        user_conf: 用户配置字典

    Returns:
        tuple[int, dict]: (score, details)
    """
    # 0. Conf处理
    merged_conf = _merge_conf(conf, user_conf)

    # 1. 小图筛选
    small_image_filter_conf = merged_conf.get("small_image_filter_conf", {})
    flag, details = _small_image_filter(task_id, small_image_filter_conf)
    if not flag:
        return 0, {**details, "failed_stage": "small_image_filter"}

    # 2. 纵图拼接
    vertical_stitch_conf = merged_conf.get("vertical_stitch_conf", {})
    flag, details = _vertical_stitch(task_id, vertical_stitch_conf)
    if not flag:
        return 0, {**details, "failed_stage": "vertical_stitch"}

    # 3. 横图拼接
    horizontal_stitch_conf = merged_conf.get("horizontal_stitch_conf", {})
    flag, details = _horizontal_stitch(task_id, horizontal_stitch_conf)
    if not flag:
        return 0, {**details, "failed_stage": "horizontal_stitch"}

    # 4. 统计总分
    calculate_total_score_conf = merged_conf.get("calculate_total_score_conf", {})
    flag, details = _calculate_total_score(task_id, calculate_total_score_conf)
    if not flag:
        return 0, {**details, "failed_stage": "calculate_total_score"}

    # TODO: 5. 整理输出 (暂不实现)

    # 当前不实装，从 conf 中获取总分
    score = 0
    return score, details


def _merge_conf(conf: dict, user_conf: dict) -> dict:
    """合并配置"""
    merged = conf.copy()
    merged.update(user_conf)
    return merged


def _small_image_filter(task_id: str, conf: dict) -> tuple[bool, dict]:
    """小图筛选"""
    # TODO: 实现小图筛选逻辑
    return True, {}


def _vertical_stitch(task_id: str, conf: dict) -> tuple[bool, dict]:
    """纵图拼接"""
    # TODO: 实现纵图拼接逻辑
    return True, {}


def _horizontal_stitch(task_id: str, conf: dict) -> tuple[bool, dict]:
    """横图拼接"""
    # TODO: 实现横图拼接逻辑
    return True, {}


def _calculate_total_score(task_id: str, conf: dict) -> tuple[bool, dict]:
    """统计总分"""
    # TODO: 实现统计总分逻辑
    return True, {}
