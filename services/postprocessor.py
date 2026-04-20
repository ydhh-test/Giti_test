# -*- coding: utf-8 -*-

"""
后处理模块

后处理主逻辑包括 10 个阶段：
1. Conf 处理
2. 小图筛选
3. 小图打分
4. 纵图拼接
5. 横图拼接
6. RIB 连续性处理（可选，由用户配置 enable_rib_continuity 控制）
7. 横图打分
8. 装饰边框
9. 统计总分
10. 整理输出
"""

import json
import shutil
from pathlib import Path
from typing import Union

from algorithms.stitching.vertical_stitch import stitch_and_resize
from configs.user_config import DEFAULT_VERTICAL_STITCH_CONF, DEFAULT_RIB_CONTINUITY_CONF
from utils.logger import get_logger

logger = get_logger("postprocessor")


# ==========================================
# Step 1: 配置处理模块内部函数
# ==========================================

def _load_user_conf(user_conf: Union[dict, str]) -> dict:
    """
    加载用户配置

    Args:
        user_conf: 用户配置，可以是 dict 或 JSON 文件路径

    Returns:
        dict: 解析后的配置字典

    Raises:
        TypeError: 如果 user_conf 类型不是 dict 或 str
        json.JSONDecodeError: 如果 JSON 解析失败
        FileNotFoundError: 如果 JSON 文件不存在
    """
    if isinstance(user_conf, dict):
        return user_conf
    elif isinstance(user_conf, str):
        # 作为 JSON 文件路径处理
        json_path = Path(user_conf)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON config file not found: {user_conf}")
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        raise TypeError(
            f"user_conf must be dict or str, got {type(user_conf).__name__}"
        )


def _merge_conf_from_complete_config(task_id: str, user_conf: dict) -> dict:
    """
    从 CompleteConfig 实例化合并配置

    Args:
        task_id: 任务 ID（用于日志或错误信息）
        user_conf: 用户配置字典

    Returns:
        dict: 合并后的配置字典
    """
    from configs import CompleteConfig

    # 实例化 CompleteConfig 获取基础配置
    complete_config = CompleteConfig()
    base_conf = complete_config.to_legacy_dict()

    # 用用户配置覆盖同名项
    merged_conf = {**base_conf, **user_conf}

    # 特殊处理 vertical_stitch_conf：深度合并
    # 用户配置覆盖默认值，但未提供的字段保留默认值
    default_vertical_conf = DEFAULT_VERTICAL_STITCH_CONF
    user_vertical_conf = user_conf.get('vertical_stitch_conf', {})

    # 深度合并：用户配置覆盖默认值
    merged_vertical_conf = {**default_vertical_conf, **user_vertical_conf}
    merged_conf['vertical_stitch_conf'] = merged_vertical_conf

    # 特殊处理 rib_continuity_conf：深度合并
    default_rib_conf = DEFAULT_RIB_CONTINUITY_CONF
    user_rib_conf = user_conf.get('rib_continuity_conf', {})
    merged_conf['rib_continuity_conf'] = {**default_rib_conf, **user_rib_conf}

    return merged_conf


def _create_error_response(task_id: str, err_msg: str, failed_stage: str) -> tuple[bool, dict]:
    """
    创建错误响应

    Args:
        task_id: 任务 ID
        err_msg: 错误信息
        failed_stage: 失败的阶段名称

    Returns:
        tuple[bool, dict]: (False, 错误详情字典)
    """
    return False, {
        "err_msg": err_msg,
        "failed_stage": failed_stage,
        "task_id": task_id
    }


# ==========================================
# Step 2: 主入口函数
# ==========================================

def postprocessor(task_id: str, user_conf: Union[dict, str]) -> tuple[bool, dict]:
    """
    后处理入口函数 - 新版本

    Args:
        task_id: 任务唯一标识
        user_conf: 用户配置（dict 或 JSON 文件路径）

    Returns:
        tuple[bool, dict]:
            成功时：(True, {image_gen_number, "0": {image_score, image_path, image_score_details}, ...})
            失败时：(False, {err_msg, failed_stage, task_id})
    """
    # Stage 1: Conf 处理
    try:
        user_conf_dict = _load_user_conf(user_conf)
        merged_conf = _merge_conf_from_complete_config(task_id, user_conf_dict)

        # 注入 decoration_conf 参数
        decoration_conf = merged_conf.get("decoration_conf", {})
        decoration_conf["tire_design_width"] = merged_conf.get("tire_design_width")
        decoration_conf["decoration_border_alpha"] = merged_conf.get("decoration_border_alpha")
        decoration_conf["decoration_gray_color"] = merged_conf.get("decoration_gray_color")
        decoration_conf["decoration_style"] = merged_conf.get("decoration_style")
        merged_conf["decoration_conf"] = decoration_conf
    except Exception as e:
        return _create_error_response(task_id, str(e), "conf_processing")

    # Stage 2: 小图筛选
    small_image_filter_conf = merged_conf.get("small_image_filter_conf", {})
    flag, details = _small_image_filter(task_id, small_image_filter_conf)
    if not flag:
        return False, {**details, "failed_stage": "small_image_filter", "task_id": task_id}

    # Stage 3: 小图打分（Rule 11 纵向细沟 & 纵向钢片检测）
    small_image_score_conf = merged_conf.get("longitudinal_grooves_conf", {})
    flag, details = _small_image_score(task_id, small_image_score_conf)
    if not flag:
        return False, {**details, "failed_stage": "small_image_score", "task_id": task_id}

    # Stage 4: 纵图拼接
    vertical_stitch_conf = merged_conf.get("vertical_stitch_conf", {})
    flag, details = _vertical_stitch(task_id, vertical_stitch_conf)
    if not flag:
        return False, {**details, "failed_stage": "vertical_stitch", "task_id": task_id}

    # Stage 5: 横图拼接（始终执行）
    horizontal_stitch_conf = merged_conf.get("horizontal_stitch_conf", {})
    flag, details = _horizontal_stitch(task_id, horizontal_stitch_conf)
    if not flag:
        return False, {**details, "failed_stage": "horizontal_stitch", "task_id": task_id}

    # Stage 6: RIB 连续性处理（可选，由用户配置控制）
    # 后续阶段的输入目录取决于本阶段是否执行
    horizontal_output_dir = "combine_horizontal"
    if merged_conf.get("enable_rib_continuity"):
        rib_continuity_conf = dict(merged_conf.get("rib_continuity_conf", {}))
        rib_continuity_conf["input_dir"] = "combine_horizontal"
        rib_continuity_conf["output_dir"] = "rib_continuity"
        flag, details = _rib_continuity_stitch(task_id, rib_continuity_conf)
        if not flag:
            return False, {**details, "failed_stage": "rib_continuity_stitch", "task_id": task_id}
        horizontal_output_dir = "rib_continuity"

    # Stage 7: 横图打分
    horizontal_image_score_conf = merged_conf.get("horizontal_image_score_conf", {})
    horizontal_image_score_conf["input_dir"] = horizontal_output_dir
    flag, details = _horizontal_image_score(task_id, horizontal_image_score_conf)
    if not flag:
        return False, {**details, "failed_stage": "horizontal_image_score", "task_id": task_id}

    # Stage 8: 装饰边框
    decoration_conf = merged_conf.get("decoration_conf", {})
    decoration_conf["input_dir"] = horizontal_output_dir
    flag, details = _add_decoration_borders(task_id, decoration_conf)
    if not flag:
        return False, {**details, "failed_stage": "decoration_borders", "task_id": task_id}

    # Stage 9: 统计总分
    calculate_total_score_conf = merged_conf.get("calculate_total_score_conf", {})
    flag, details = _calculate_total_score(task_id, calculate_total_score_conf)
    if not flag:
        return False, {**details, "failed_stage": "calculate_total_score", "task_id": task_id}

    # Stage 10: 整理输出
    standard_input_conf = merged_conf.get("standard_input_conf", {})
    flag, details = _standard_input(task_id, standard_input_conf, details)
    if not flag:
        return False, {**details, "failed_stage": "standard_input", "task_id": task_id}

    return True, details


# ==========================================
# Step 3: 9 个阶段的内部函数
# ==========================================

def _build_vertical_stitch_filters(vertical_stitch_conf: dict) -> list:
    """
    基于 filter_output_dirs 构建纵图拼接 filters 列表

    Args:
        vertical_stitch_conf: 纵图拼接配置（已合并默认值）
            - center_vertical.resolution: center 方向分辨率
            - side_vertical.resolution: side 方向分辨率
            - center_count: center 方向拼接数量
            - side_count: side 方向拼接数量

    Returns:
        list: filters 列表

    Raises:
        ValueError: 如果配置缺失
    """
    from configs.base_config import SystemConfig

    # 获取 filter_output_dirs（和小图筛选使用同一个配置）
    system_config = SystemConfig()
    filter_output_dirs = system_config.filter_output_dirs

    # 配置校验：不能为空
    if not vertical_stitch_conf:
        raise ValueError("vertical_stitch_conf 不能为空")

    # 遍历 filter_output_dirs，生成 filters
    filters = []
    for filter_dir in filter_output_dirs:
        # 从 filter_dir 提取 base_type: center_filter → center, side_filter → side
        base_type = filter_dir.replace('_filter', '')

        # 从配置中获取该方向的参数
        vertical_key = f"{base_type}_vertical"
        count_key = f"{base_type}_count"

        # 获取分辨率 - 缺少则报错
        vertical_conf = vertical_stitch_conf.get(vertical_key, {})
        resolution = vertical_conf.get("resolution")

        if resolution is None:
            raise ValueError(f"配置缺少 {vertical_key}.resolution")

        # 获取拼接数量 - 缺少则报错
        stitch_count = vertical_stitch_conf.get(count_key)

        if stitch_count is None:
            raise ValueError(f"配置缺少 {count_key}")

        filters.append({
            "dir": filter_dir,
            "stitch_count": stitch_count,
            "resolution": resolution
        })

    return filters


def _small_image_filter(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    小图筛选阶段

    流程:
    1. 从 SystemConfig 获取 inf_output_dirs 和 filter_output_dirs
    2. 复制图片 inf → filter
    3. 调用 rule6_1::process_pattern_continuity()
    4. 返回结果

    Args:
        task_id: 任务 ID
        conf: 小图筛选配置

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from configs.base_config import SystemConfig
    from rules.rule6_1 import process_pattern_continuity
    from pathlib import Path
    import shutil

    # 获取系统配置
    system_config = SystemConfig()
    inf_output_dirs = system_config.inf_output_dirs
    filter_output_dirs = system_config.filter_output_dirs

    # 构建基础路径
    base_path = Path(".results") / f"task_id_{task_id}"

    # Step 1: 复制图片 (inf → filter)
    for inf_dir, filter_dir in zip(inf_output_dirs, filter_output_dirs):
        src_dir = base_path / inf_dir
        dst_dir = base_path / filter_dir

        if src_dir.exists():
            _copy_images(src_dir, dst_dir)
        else:
            logger.warning(f"源目录不存在，跳过：{src_dir}")

    # Step 2: 调用图案连续性检测
    flag, details = process_pattern_continuity(task_id, conf)

    if not flag:
        return False, {
            "err_msg": details.get("err_msg", "图案连续性检测失败"),
            "task_id": task_id,
            "failed_stage": "pattern_continuity"
        }

    # 返回结果
    summary = details.get("summary", {})
    return True, {
        "task_id": task_id,
        "pattern_continuity_stats": details,
        "image_gen_number": summary.get("total_kept", 0),
        "total_deleted": summary.get("total_deleted", 0)
    }


def _copy_images(src_dir: Path, dst_dir: Path) -> None:
    """辅助函数：复制图片"""
    if not src_dir.exists():
        return

    dst_dir.mkdir(parents=True, exist_ok=True)

    extensions = ['.png', '.jpg', '.jpeg', '.bmp']
    for ext in extensions:
        for img_file in src_dir.glob(f"*{ext}"):
            shutil.copy2(str(img_file), str(dst_dir / img_file.name))


def _small_image_score(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    小图打分阶段（Rule 11 纵向细沟 & 纵向钢片检测）

    Args:
        task_id: 任务 ID
        conf: 纵向细沟检测配置（来自 LongitudinalGroovesConfig）

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from rules.rule11 import process_longitudinal_grooves

    return process_longitudinal_grooves(task_id, conf)


def _vertical_stitch(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    纵图拼接阶段

    Args:
        task_id: 任务 ID
        conf: 纵图拼接配置（已合并默认值）

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from rules.rule6_2 import process_vertical_stitch

    # conf 已经是纵图拼接配置内容本身，直接使用
    vertical_stitch_conf = conf

    # 配置校验：不能为空
    if not vertical_stitch_conf:
        return False, {
            "err_msg": "vertical_stitch_conf 不能为空",
            "task_id": task_id
        }

    # 构建 filters 列表（基于 filter_output_dirs）
    try:
        filters = _build_vertical_stitch_filters(vertical_stitch_conf)
    except ValueError as e:
        return False, {
            "err_msg": str(e),
            "task_id": task_id
        }

    # 构建完整的配置传递给 rule6_2
    vertical_stitch_full_conf = {
        "base_path": ".results",
        "filters": filters,
        "output_dir_suffix": "_vertical",
    }

    return process_vertical_stitch(task_id, vertical_stitch_full_conf)


def _horizontal_stitch(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    横图拼接阶段

    Args:
        task_id: 任务 ID
        conf: 横图拼接配置 (扁平配置)

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from rules.rule1to5 import process_horizontal_stitch

    # conf 已经是扁平配置，直接传递给中间层
    return process_horizontal_stitch(task_id, conf)


def _rib_continuity_stitch(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    RIB 连续性处理阶段（从横图拼接结果切分 RIB 后重新拼接）

    Args:
        task_id: 任务 ID
        conf: rib_continuity 配置字典
            - input_dir: 横图拼接输出目录（默认 "combine_horizontal"）
            - output_dir: 输出目录（默认 "rib_continuity"）
            - continuity_mode, groove_width_mm, pixel_per_mm, blend_width, edge_continuity

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from rules.rule12_16_17 import process_rib_continuity_from_horizontal

    return process_rib_continuity_from_horizontal(task_id, conf)


def _horizontal_image_score(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    横图打分阶段

    Args:
        task_id: 任务 ID
        conf: 横图打分配置

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from rules.rule13 import process_horizontal_image_score

    # 调用 rule13 中间层
    flag, details = process_horizontal_image_score(task_id, conf)

    if not flag:
        return False, {
            "err_msg": details.get("err_msg", "横图打分失败"),
            "task_id": task_id
        }

    # 提取图片数量信息
    summary = details.get("summary", {})
    return True, {
        "task_id": task_id,
        "horizontal_image_score_stats": details,
        "image_gen_number": summary.get("total_scored", 0),
        "total_score": summary.get("total_score", 0)
    }


def _calculate_total_score(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    统计总分阶段

    Args:
        task_id: 任务 ID
        conf: 评分配置

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    # TODO: 聚合前序阶段的评分结果
    # 不再调用 compute_land_sea_ratio
    return True, {"total_score": 0, "task_id": task_id}


def _standard_input(task_id: str, conf: dict, details: dict) -> tuple[bool, dict]:
    """
    整理输出阶段

    Args:
        task_id: 任务 ID
        conf: 整理输出配置
        details: 前序阶段传递的详情字典

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    # TODO: 实现整理输出逻辑
    # 按得分排序（高分优先，同分按文件名字母序）
    return True, details


# ==========================================
# Step 4: 适配现有 _add_decoration_borders 函数
# ==========================================

def _add_decoration_borders(task_id: str, decoration_conf: dict) -> tuple[bool, dict]:
    """
    添加装饰边框 - 调用 rule19 中间层

    Args:
        task_id: 任务 ID
        decoration_conf: 装饰边框配置 (已注入 tire_design_width 等参数)

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from rules.rule19 import process_decoration_borders

    # 调用 rule19 中间层
    flag, details = process_decoration_borders(task_id, decoration_conf)

    if not flag:
        return False, {
            "err_msg": details.get("err_msg", "装饰边框处理失败"),
            "task_id": task_id
        }

    # 将 rule19 返回格式转换为 postprocessor 需要的格式
    output_dir = decoration_conf.get("output_dir", "combine")
    images_dict = details.get("directories", {}).get(output_dir, {}).get("images", {})

    # 构建符合 postprocessor 格式的 details
    image_gen_number = len([img for img in images_dict.values() if img.get("status") == "success"])

    converted_details = {
        "image_gen_number": image_gen_number,
        "decoration_style": decoration_conf.get("decoration_style", "simple"),
        "tdw": decoration_conf.get("tire_design_width"),
        "alpha": decoration_conf.get("decoration_border_alpha", 0.5)
    }

    # 按文件名字母序添加每张图片信息
    sorted_images = sorted(
        [(name, img) for name, img in images_dict.items() if img.get("status") == "success"],
        key=lambda x: x[0]
    )

    for idx, (image_name, image_data) in enumerate(sorted_images):
        converted_details[str(idx)] = {
            "image_score": 0.0,  # 暂时填 0.0，留给后续阶段填充
            "image_path": image_data.get("output_path", ""),
            "image_score_details": None  # 暂时填 None，留给后续阶段填充
        }

    return True, converted_details
