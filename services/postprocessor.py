# -*- coding: utf-8 -*-

"""
后处理模块

后处理主逻辑包括：
1，小图筛选阶段
2，拼图阶段
3，大图打分阶段
4，输出整理阶段
"""


from algorithms.stitching.vertical_stitch import VerticalStitch


def postprocessor(task_id: str, conf: dict, user_conf: dict) -> tuple[int, dict]:
    """
    后处理入口函数

    Args:
        task_id: 任务ID
        conf: 配置字典（支持旧格式和新格式）
        user_conf: 用户配置字典

    Returns:
        tuple[int, dict]: (score, details)
    """
    # 0. Conf处理 - 向后兼容处理
    try:
        from configs import CompleteConfig
        if isinstance(conf, CompleteConfig):
            merged_conf = {**conf.to_legacy_dict(), **user_conf}
        else:
            merged_conf = _merge_conf(conf, user_conf)
    except ImportError:
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

    # 4. 装饰边框
    decoration_conf = merged_conf.get("decoration_conf", {})
    flag, details = _add_decoration_borders(task_id, decoration_conf, merged_conf)
    if not flag:
        return 0, {**details, "failed_stage": "decoration_borders"}

    # 5. 统计总分
    calculate_total_score_conf = merged_conf.get("calculate_total_score_conf", {})
    flag, details = _calculate_total_score(task_id, calculate_total_score_conf)
    if not flag:
        return 0, {**details, "failed_stage": "calculate_total_score"}

    # TODO: 6. 整理输出 (暂不实现)

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
    # 传递完整的配置给VerticalStitch，以便访问所有配置参数
    stitcher = VerticalStitch(task_id, conf)
    return stitcher.process()


def _horizontal_stitch(task_id: str, conf: dict) -> tuple[bool, dict]:
    """横图拼接"""
    from algorithms.stitching.horizontal_stitch import HorizontalStitch
    stitcher = HorizontalStitch(task_id, conf)
    return stitcher.process()


def _calculate_total_score(task_id: str, conf: dict) -> tuple[bool, dict]:
    """统计总分"""
    from rules.scoring.land_sea_ratio import compute_land_sea_ratio
    from pathlib import Path
    import cv2

    # 1. 确定图片路径
    image_path = conf.get('image_path')
    if not image_path:
        # 默认使用装饰边框后的图片
        base_path = Path(".results") / task_id / "rst"
        if not base_path.exists():
            return False, {"error": f"rst directory not found: {base_path}"}

        # 获取第一个图片文件
        image_files = list(base_path.glob("*.png"))
        if not image_files:
            return False, {"error": "No images found in rst directory"}
        image_path = str(image_files[0])

    # 2. 读取图片
    img = cv2.imread(image_path)
    if img is None:
        return False, {"error": f"Failed to read image: {image_path}"}

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


def _add_decoration_borders(task_id: str, conf: dict, merged_conf: dict) -> tuple[bool, dict]:
    """
    添加装饰边框

    Args:
        task_id: 任务ID
        conf: 装饰边框配置
        merged_conf: 完整配置（包含用户配置）

    Returns:
        tuple[bool, dict]: (是否成功, 详情字典)
    """
    from utils.cv_utils import add_gray_borders
    from pathlib import Path
    import cv2

    # 1. 检查必需配置
    if 'tire_design_width' not in merged_conf:
        return False, {"error": "tire_design_width not configured"}

    # 2. 确定输入输出路径
    base_path = Path(".results") / task_id
    combine_dir = base_path / "combine"
    rst_dir = base_path / "rst"
    rst_dir.mkdir(parents=True, exist_ok=True)

    # 3. 检查输入目录
    if not combine_dir.exists():
        return False, {"error": f"combine directory not found: {combine_dir}"}

    # 4. 处理所有拼接完成的大图
    processed_files = []
    decoration_style = merged_conf.get('decoration_style', 'simple')

    for img_path in combine_dir.glob("*.png"):
        try:
            # 根据装饰风格选择处理方式
            if decoration_style == 'simple':
                # 调用add_gray_borders，传入conf
                result = add_gray_borders(str(img_path), merged_conf)
            else:
                # 未来可以扩展其他风格
                return False, {"error": f"Unsupported decoration_style: {decoration_style}"}

            # 保存结果
            output_path = rst_dir / img_path.name
            cv2.imwrite(str(output_path), result)
            processed_files.append(str(output_path))

        except Exception as e:
            return False, {"error": f"Failed to process {img_path}: {str(e)}"}

    return True, {
        "processed_files": processed_files,
        "decoration_style": decoration_style,
        "tdw": merged_conf.get('tire_design_width'),
        "alpha": merged_conf.get('decoration_border_alpha', 0.5)
    }
