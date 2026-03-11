# -*- coding: utf-8 -*-
"""
rule13: 横图打分中间层

功能:
- 接收 postprocessor 的调用
- 循环 combine_horizontal 目录中的所有图片
- 调用 compute_land_sea_ratio() 进行海陆比评分
- 保存评分结果和可视化结果

目录关系:
- 输入：.results/task_id_{task_id}/combine_horizontal/{image_name}.png
- 可视化输出：.results/task_id_{task_id}/rule13/{image_name}.png
- 评分结果 JSON: .results/task_id_{task_id}/scores/rule13/{image_name}.json
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple
import cv2
import json
import numpy as np

from utils.logger import get_logger

logger = get_logger("rule13")


def process_horizontal_image_score(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    横图打分主入口

    参数:
        task_id: 任务 ID
        conf: 配置字典
            - input_dir: 输入目录名 (可选，默认 "combine_horizontal")
            - land_sea_ratio: 海陆比算法配置
            - visualize: 是否生成可视化 (可选，默认 True)
            - output_base_dir: 输出基础目录 (可选，默认 ".results")

    返回:
        (True, 详细统计字典) 或 (False, 错误信息)
    """
    # 从 conf 读取配置参数
    input_dir = conf.get("input_dir", "combine_horizontal")
    land_sea_ratio_conf = conf.get("land_sea_ratio", {})
    visualize = conf.get("visualize", True)
    output_base_dir = conf.get("output_base_dir", ".results")

    # 构建输入目录路径
    base_path = Path(output_base_dir) / f"task_id_{task_id}"
    dir_path = base_path / input_dir

    # 检查目录是否存在
    if not dir_path.exists():
        logger.warning(f"目录不存在，跳过：{dir_path}")
        return True, {
            "task_id": task_id,
            "directories": {
                input_dir: {
                    "total_count": 0,
                    "scored_count": 0,
                    "failed_count": 0,
                    "total_score": 0,
                    "images": {}
                }
            },
            "summary": {
                "total_images": 0,
                "total_scored": 0,
                "total_failed": 0,
                "total_score": 0
            }
        }

    # 获取图片列表
    image_files = _get_image_files(dir_path)

    if not image_files:
        logger.warning(f"目录为空：{dir_path}")
        return True, {
            "task_id": task_id,
            "directories": {
                input_dir: {
                    "total_count": 0,
                    "scored_count": 0,
                    "failed_count": 0,
                    "total_score": 0,
                    "images": {}
                }
            },
            "summary": {
                "total_images": 0,
                "total_scored": 0,
                "total_failed": 0,
                "total_score": 0
            }
        }

    # 循环处理每张图片
    image_results = []
    images_dict = {}

    for image_id, image_path in enumerate(image_files):
        flag, result = process_single_image(
            image_path=image_path,
            task_id=task_id,
            conf=conf,
            image_id=image_id
        )

        if flag:
            image_results.append(result)
            images_dict[image_path.name] = result
        else:
            # 处理失败
            image_results.append({
                "image_name": image_path.name,
                "image_id": str(image_id),
                "status": "failed",
                "error": result.get("err_msg", "未知错误")
            })
            images_dict[image_path.name] = {
                "status": "failed",
                "error": result.get("err_msg", "未知错误")
            }
            logger.error(f"处理图片失败 {image_path.name}: {result.get('err_msg', '未知错误')}")

    # 聚合统计信息
    summary = _aggregate_summary(image_results)

    return True, {
        "task_id": task_id,
        "directories": {
            input_dir: {
                "total_count": len(image_files),
                "scored_count": summary["total_scored"],
                "failed_count": summary["total_failed"],
                "total_score": summary["total_score"],
                "images": images_dict
            }
        },
        "summary": summary
    }


def process_single_image(
    image_path: Path,
    task_id: str,
    conf: dict,
    image_id: int
) -> Tuple[bool, Dict[str, Any]]:
    """
    对单张图片进行海陆比评分

    参数:
        image_path: 图片路径
        task_id: 任务 ID
        conf: 配置字典
        image_id: 图片序号 (用于日志和追踪)

    返回:
        (True, 单张图片评分结果) 或 (False, 错误信息)
    """
    from rules.scoring.land_sea_ratio import compute_land_sea_ratio

    try:
        # 读取图片
        img = cv2.imread(str(image_path))
        if img is None:
            return False, {"err_msg": "图片读取失败"}

        # 获取配置
        land_sea_ratio_conf = conf.get("land_sea_ratio", {})
        visualize = conf.get("visualize", True)
        output_base_dir = conf.get("output_base_dir", ".results")

        # 调用海陆比算法
        score, details = compute_land_sea_ratio(img, land_sea_ratio_conf)

        # 获取海陆比值
        ratio = details.get("ratio_value", 0.0)

        # 构建输出路径
        base_path = Path(output_base_dir) / f"task_id_{task_id}"
        vis_output_dir = base_path / "rule13"
        json_output_dir = base_path / "scores" / "rule13"

        vis_output_path = vis_output_dir / image_path.name
        json_output_path = json_output_dir / f"{image_path.name}.json"

        # 如果 visualize=True，生成可视化
        if visualize:
            visualize_score(img, score, ratio, vis_output_path)

        # 构建评分结果数据
        score_data = {
            "task_id": task_id,
            "image_name": image_path.name,
            "image_id": str(image_id),
            "score": score,
            "land_sea_ratio": ratio,
            "status": "success",
            "details": details,
            "vis_path": str(vis_output_path) if visualize else None,
            "json_path": str(json_output_path)
        }

        # 保存 JSON
        save_score_json(score_data, json_output_path)

        return True, score_data

    except Exception as e:
        logger.error(f"处理图片 {image_path.name} 异常：{str(e)}")
        return False, {"err_msg": str(e)}


def visualize_score(image: np.ndarray, score: int, ratio: float, output_path: Path) -> None:
    """
    在新图上标注海陆比分数，并用颜色标识黑色和灰色区域

    流程:
    1. 创建图片副本
    2. 获取黑色和灰色区域掩码
    3. 在副本上叠加颜色层：
       - 黑色区域 → 红色半透明叠加
       - 灰色区域 → 绿色半透明叠加
    4. 计算自适应字体大小 (基于图片宽度/高度)
    5. 计算自适应文字颜色 (根据背景亮度)
    6. 在左上角绘制标注文字
    7. 保存结果
    """
    # Step 1: 创建副本
    vis_img = image.copy()

    # Step 2: 获取灰度图
    gray = cv2.cvtColor(vis_img, cv2.COLOR_BGR2GRAY) if len(vis_img.shape) == 3 else vis_img

    # Step 3: 获取黑色和灰色区域掩码
    black_mask = cv2.inRange(gray, 0, 50)      # 黑色区域阈值
    gray_mask = cv2.inRange(gray, 51, 200)     # 灰色区域阈值

    # Step 4: 叠加颜色层
    # 红色叠加层 (黑色区域) - BGR 格式
    red_overlay = np.zeros_like(vis_img)
    red_overlay[:, :] = (0, 0, 255)  # BGR 红色

    # 使用位运算和加权叠加
    red_masked = cv2.bitwise_and(red_overlay, red_overlay, mask=black_mask)
    vis_img = cv2.addWeighted(vis_img, 1.0, red_masked, 0.5, 0)

    # 绿色叠加层 (灰色区域) - BGR 格式
    green_overlay = np.zeros_like(vis_img)
    green_overlay[:, :] = (0, 255, 0)  # BGR 绿色

    green_masked = cv2.bitwise_and(green_overlay, green_overlay, mask=gray_mask)
    vis_img = cv2.addWeighted(vis_img, 1.0, green_masked, 0.5, 0)

    # Step 5: 自适应字体大小
    height, width = vis_img.shape[:2]
    font_scale = min(width, height) / 500  # 自适应系数
    # 设置字体大小上下限
    font_scale = max(0.5, min(2.0, font_scale))

    # Step 6: 自适应文字颜色
    # 检查左上角区域亮度
    roi_height = max(1, min(100, height // 10))
    roi_width = max(1, min(200, width // 5))
    roi = gray[0:roi_height, 0:roi_width]
    avg_brightness = np.mean(roi)
    text_color = (0, 0, 0) if avg_brightness > 128 else (255, 255, 255)

    # Step 7: 绘制标注文字
    text1 = f"海陆比：{ratio:.2f}%"
    text2 = f"评分：{score}"

    y_offset = int(30 * font_scale)
    thickness = max(1, int(2 * font_scale))

    cv2.putText(vis_img, text1, (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness)
    cv2.putText(vis_img, text2, (10, int(y_offset * 2.5)),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness)

    # Step 8: 保存结果
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), vis_img)


def save_score_json(score_data: dict, output_path: Path) -> None:
    """
    保存单张图片的评分结果为 JSON 文件

    参数:
        score_data: 评分数据字典
        output_path: JSON 文件输出路径
    """
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入 JSON 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(score_data, f, indent=2, ensure_ascii=False)


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
    scored_count = sum(1 for r in image_results if r.get("status") == "success")
    failed_count = total_count - scored_count
    total_score = sum(r.get("score", 0) for r in image_results if r.get("status") == "success")

    return {
        "total_images": total_count,
        "total_scored": scored_count,
        "total_failed": failed_count,
        "total_score": total_score
    }
