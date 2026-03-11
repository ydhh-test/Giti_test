# -*- coding: utf-8 -*-

"""
后处理模块

后处理主逻辑包括 9 个阶段：
1. Conf 处理
2. 小图筛选
3. 小图打分
4. 纵图拼接
5. 横图拼接
6. 横图打分
7. 装饰边框
8. 统计总分
9. 整理输出
"""

import json
import shutil
from pathlib import Path
from typing import Union

from algorithms.stitching.vertical_stitch import stitch_and_resize
from configs.user_config import DEFAULT_VERTICAL_STITCH_CONF
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
    except Exception as e:
        return _create_error_response(task_id, str(e), "conf_processing")

    # Stage 2: 小图筛选
    small_image_filter_conf = merged_conf.get("small_image_filter_conf", {})
    flag, details = _small_image_filter(task_id, small_image_filter_conf)
    if not flag:
        return False, {**details, "failed_stage": "small_image_filter", "task_id": task_id}

    # Stage 3: 小图打分
    small_image_score_conf = merged_conf.get("small_image_score_conf", {})
    flag, details = _small_image_score(task_id, small_image_score_conf)
    if not flag:
        return False, {**details, "failed_stage": "small_image_score", "task_id": task_id}

    # Stage 4: 纵图拼接
    vertical_stitch_conf = merged_conf.get("vertical_stitch_conf", {})
    flag, details = _vertical_stitch(task_id, vertical_stitch_conf)
    if not flag:
        return False, {**details, "failed_stage": "vertical_stitch", "task_id": task_id}

    # Stage 5: 横图拼接
    horizontal_stitch_conf = merged_conf.get("horizontal_stitch_conf", {})
    flag, details = _horizontal_stitch(task_id, horizontal_stitch_conf)
    if not flag:
        return False, {**details, "failed_stage": "horizontal_stitch", "task_id": task_id}

    # Stage 6: 横图打分
    horizontal_image_score_conf = merged_conf.get("horizontal_image_score_conf", {})
    flag, details = _horizontal_image_score(task_id, horizontal_image_score_conf)
    if not flag:
        return False, {**details, "failed_stage": "horizontal_image_score", "task_id": task_id}

    # Stage 7: 装饰边框
    decoration_conf = merged_conf.get("decoration_conf", {})
    flag, details = _add_decoration_borders(task_id, decoration_conf, merged_conf)
    if not flag:
        return False, {**details, "failed_stage": "decoration_borders", "task_id": task_id}

    # Stage 8: 统计总分
    calculate_total_score_conf = merged_conf.get("calculate_total_score_conf", {})
    flag, details = _calculate_total_score(task_id, calculate_total_score_conf)
    if not flag:
        return False, {**details, "failed_stage": "calculate_total_score", "task_id": task_id}

    # Stage 9: 整理输出
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
    小图打分阶段

    Args:
        task_id: 任务 ID
        conf: 小图打分配置

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    # TODO: 实现小图打分逻辑
    return True, {"image_gen_number": 0, "task_id": task_id}


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


def _horizontal_image_score(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    横图打分阶段

    Args:
        task_id: 任务 ID
        conf: 横图打分配置

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    # TODO: 实现横图打分逻辑
    return True, {"image_gen_number": 0, "task_id": task_id}


def _calculate_total_score(task_id: str, conf: dict) -> tuple[bool, dict]:
    """
    统计总分阶段

    Args:
        task_id: 任务 ID
        conf: 评分配置

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from rules.scoring.land_sea_ratio import compute_land_sea_ratio
    import cv2

    # 1. 确定图片路径
    image_path = conf.get('image_path')
    if not image_path:
        # 默认使用装饰边框后的图片
        base_path = Path(".results") / task_id / "rst"
        if not base_path.exists():
            return False, {"err_msg": f"rst directory not found: {base_path}", "task_id": task_id}

        # 获取第一个图片文件
        image_files = list(base_path.glob("*.png"))
        if not image_files:
            return False, {"err_msg": "No images found in rst directory", "task_id": task_id}
        image_path = str(image_files[0])

    # 2. 读取图片
    img = cv2.imread(image_path)
    if img is None:
        return False, {"err_msg": f"Failed to read image: {image_path}", "task_id": task_id}

    # 3. 计算海陆比评分
    land_sea_conf = conf.get('land_sea_ratio', {})
    land_sea_score, land_sea_details = compute_land_sea_ratio(img, land_sea_conf)

    # 4. 聚合总分
    details = {
        "total_score": land_sea_score,
        "image_path": image_path,
        "scoring_items": {
            "land_sea_ratio": {
                "score": land_sea_score,
                "details": land_sea_details
            }
        }
    }

    return True, details


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

def _add_decoration_borders(task_id: str, conf: dict, merged_conf: dict) -> tuple[bool, dict]:
    """
    添加装饰边框

    Args:
        task_id: 任务 ID
        conf: 装饰边框配置
        merged_conf: 完整配置（包含用户配置）

    Returns:
        tuple[bool, dict]: (是否成功，详情字典)
    """
    from utils.cv_utils import add_gray_borders
    import cv2

    # 1. 检查必需配置
    if 'tire_design_width' not in merged_conf:
        return False, {"err_msg": "tire_design_width not configured", "task_id": task_id}

    # 2. 确定输入输出路径
    base_path = Path(".results") / task_id
    combine_dir = base_path / "combine"
    rst_dir = base_path / "rst"
    rst_dir.mkdir(parents=True, exist_ok=True)

    # 3. 检查输入目录
    if not combine_dir.exists():
        return False, {"err_msg": f"combine directory not found: {combine_dir}", "task_id": task_id}

    # 4. 处理所有拼接完成的大图
    processed_files = []
    decoration_style = merged_conf.get('decoration_style', 'simple')

    for img_path in combine_dir.glob("*.png"):
        try:
            # 根据装饰风格选择处理方式
            if decoration_style == 'simple':
                # 调用 add_gray_borders，传入 conf
                result = add_gray_borders(str(img_path), merged_conf)
            else:
                # 未来可以扩展其他风格
                return False, {"err_msg": f"Unsupported decoration_style: {decoration_style}", "task_id": task_id}

            # 保存结果
            output_path = rst_dir / img_path.name
            cv2.imwrite(str(output_path), result)
            processed_files.append(str(output_path))

        except Exception as e:
            return False, {"err_msg": f"Failed to process {img_path}: {str(e)}", "task_id": task_id}

    # 构建符合新返回格式的 details
    image_gen_number = len(processed_files)
    details = {
        "image_gen_number": image_gen_number,
        "processed_files": processed_files,
        "decoration_style": decoration_style,
        "tdw": merged_conf.get('tire_design_width'),
        "alpha": merged_conf.get('decoration_border_alpha', 0.5)
    }

    # 为每张图片添加信息（按文件名字母序）
    sorted_files = sorted(processed_files)
    for idx, file_path in enumerate(sorted_files):
        details[str(idx)] = {
            "image_score": 0.0,  # 待后续阶段填充
            "image_path": file_path,
            "image_score_details": None
        }

    return True, details
