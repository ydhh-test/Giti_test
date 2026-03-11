# -*- coding: utf-8 -*-
"""
rule19: 装饰边框中间层

功能:
- 接收 postprocessor 的调用
- 循环 input_dir 目录中的所有图片
- 调用 add_gray_borders() 添加装饰边框
- 保存到 output_dir 目录

目录关系:
- 输入：.results/task_id_{task_id}/{input_dir}/*.png
- 输出：.results/task_id_{task_id}/{output_dir}/*.png
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple
import cv2

from utils.logger import get_logger

logger = get_logger("rule19")


def process_decoration_borders(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    装饰边框主入口

    参数:
        task_id: 任务 ID
        conf: 配置字典
            - input_dir: 输入目录名 (默认 "combine_horizontal")
            - output_dir: 输出目录名 (默认 "combine")
            - tire_design_width: 花纹有效宽度 (像素)
            - decoration_border_alpha: 透明度 (0~1)
            - decoration_gray_color: 灰色 RGB 值
            - output_base_dir: 输出基础目录 (默认 ".results")

    返回:
        (True, 详细统计字典) 或 (False, 错误信息)
    """
    # Step 1: 从 conf 读取配置参数
    input_dir = conf.get("input_dir", "combine_horizontal")
    output_dir = conf.get("output_dir", "combine")
    output_base_dir = conf.get("output_base_dir", ".results")

    # Step 2: 构建输入输出路径
    base_path = Path(output_base_dir) / f"task_id_{task_id}"
    input_path = base_path / input_dir
    output_path = base_path / output_dir

    # Step 3: 检查输入目录是否存在
    if not input_path.exists():
        # 目录不存在，返回空统计
        return True, _build_empty_result(input_dir)

    # Step 4: 获取图片列表
    image_files = _get_image_files(input_path)

    if not image_files:
        # 目录为空，返回空统计
        return True, _build_empty_result(input_dir)

    # Step 5: 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)

    # Step 6: 循环处理每张图片
    image_results = []
    images_dict = {}

    for image_id, image_file in enumerate(image_files):
        flag, result = process_single_image(
            image_path=image_file,
            task_id=task_id,
            conf=conf,
            image_id=image_id,
            output_dir=output_path
        )

        if flag:
            image_results.append(result)
            images_dict[image_file.name] = result
        else:
            # 处理失败
            images_dict[image_file.name] = {
                "status": "failed",
                "error": result.get("err_msg", "未知错误")
            }
            logger.error(f"处理图片失败 {image_file.name}: {result.get('err_msg', '未知错误')}")

    # Step 7: 聚合统计信息
    summary = _aggregate_summary(image_results)

    return True, {
        "task_id": task_id,
        "directories": {
            output_dir: {
                "total_count": len(image_files),
                "processed_count": summary["total_processed"],
                "failed_count": summary["total_failed"],
                "images": images_dict
            }
        },
        "summary": summary
    }


def process_single_image(
    image_path: Path,
    task_id: str,
    conf: dict,
    image_id: int,
    output_dir: Path
) -> Tuple[bool, Dict[str, Any]]:
    """
    单张图片装饰边框处理

    参数:
        image_path: 图片路径
        task_id: 任务 ID
        conf: 配置字典
        image_id: 图片序号
        output_dir: 输出目录

    返回:
        (True, 处理结果) 或 (False, 错误信息)
    """
    from utils.cv_utils import add_gray_borders

    try:
        # Step 1: 读取图片
        img = cv2.imread(str(image_path))
        if img is None:
            return False, {"err_msg": "图片读取失败"}

        # Step 2: 调用 add_gray_borders
        result_img = add_gray_borders(img, conf)

        # Step 3: 保存结果
        output_path = output_dir / image_path.name
        cv2.imwrite(str(output_path), result_img)

        # Step 4: 构建返回结果
        return True, {
            "image_id": str(image_id),
            "image_name": image_path.name,
            "status": "success",
            "input_path": str(image_path),
            "output_path": str(output_path)
        }

    except Exception as e:
        logger.error(f"处理图片 {image_path.name} 异常：{str(e)}")
        return False, {"err_msg": str(e)}


# ========== 辅助函数 ==========

def _get_image_files(dir_path: Path) -> List[Path]:
    """获取目录内所有图片文件，按文件名排序"""
    extensions = ['.png', '.jpg', '.jpeg', '.bmp']
    image_files = []
    for ext in extensions:
        image_files.extend(dir_path.glob(f"*{ext}"))
    return sorted(image_files, key=lambda x: x.name)


def _aggregate_summary(image_results: List[Dict[str, Any]]) -> dict:
    """聚合所有图片的统计信息"""
    total_count = len(image_results)
    processed_count = sum(1 for r in image_results if r.get("status") == "success")
    failed_count = total_count - processed_count

    return {
        "total_images": total_count,
        "total_processed": processed_count,
        "total_failed": failed_count
    }


def _build_empty_result(input_dir: str) -> dict:
    """构建空结果"""
    return {
        "task_id": None,
        "directories": {
            input_dir: {
                "total_count": 0,
                "processed_count": 0,
                "failed_count": 0,
                "images": {}
            }
        },
        "summary": {
            "total_images": 0,
            "total_processed": 0,
            "total_failed": 0
        }
    }
