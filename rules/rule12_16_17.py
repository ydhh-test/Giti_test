# -*- coding: utf-8 -*-
"""
rule12_16_17: RIB横向连续性拼接中间层

功能:
- Rule 16: RIB2/3/4横沟/钢片任意组合连续性
- Rule 17: RIB1/2和RIB4/5可连续可不连续（概率控制）

处理流程:
1. 从 center_vertical 和 side_vertical 目录读取完整 RIB 图
2. 根据连续性配置调用拼接算法
3. 输出带主沟的完整胎面图

目录关系:
- 输入：.results/task_id_{task_id}/center_vertical/
         .results/task_id_{task_id}/side_vertical/
- 输出：.results/task_id_{task_id}/{output_dir}/
"""

import cv2
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any

from algorithms.stitching.rib_continuity_stitch import stitch_with_continuity
from utils.logger import get_logger

logger = get_logger("rule12_16_17")

_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp'}


# ========== 主入口函数 ==========

def process_rib_continuity(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    Rule 12/16/17 主入口

    参数:
        task_id: 任务ID
        conf: 配置字典
            - base_path: 基础路径（默认 ".results"）
            - center_dir: center 图像子目录名（默认 "center_vertical"）
            - side_dir: side 图像子目录名（默认 "side_vertical"）
            - continuity_mode: "RIB2-RIB3" | "RIB3-RIB4" | "RIB2-RIB3-RIB4" | "none"
            - groove_width_mm: 主沟宽度(mm)，默认10.0
            - pixel_per_mm: 像素/毫米，默认2.0
            - blend_width: 融合宽度像素（默认10）
            - edge_continuity: 边缘连续性概率配置
                - "RIB1-RIB2": 0.0~1.0 概率
                - "RIB4-RIB5": 0.0~1.0 概率
            - output_dir: 输出子目录名（默认 "rule12_16_17"）

    返回:
        (True, {"task_id": ..., "output_dir": ..., "directories": {...}})
        或 (False, {"err_msg": ..., "task_id": ...})
    """
    try:
        # Step 1: 路径配置
        base_path = conf.get("base_path", ".results")
        task_dir = Path(base_path) / f"task_id_{task_id}"

        center_dir = task_dir / conf.get("center_dir", "center_vertical")
        side_dir = task_dir / conf.get("side_dir", "side_vertical")

        output_dir_name = conf.get("output_dir", "rule12_16_17")
        output_dir = task_dir / output_dir_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 2: 校验输入
        if not center_dir.exists():
            return False, {"err_msg": f"center目录不存在: {center_dir}", "task_id": task_id}
        if not side_dir.exists():
            return False, {"err_msg": f"side目录不存在: {side_dir}", "task_id": task_id}

        # Step 3: 加载图像
        center_images, center_names = _load_images(center_dir)
        side_images, side_names = _load_images(side_dir)

        if not center_images:
            return False, {"err_msg": "未找到center RIB图像", "task_id": task_id}
        if not side_images:
            return False, {"err_msg": "未找到side RIB图像", "task_id": task_id}

        # Step 4: 解析配置
        continuity_mode = conf.get("continuity_mode", "none")
        groove_width_mm = conf.get("groove_width_mm", 10.0)
        pixel_per_mm = conf.get("pixel_per_mm", 2.0)
        groove_width_px = max(1, int(round(groove_width_mm * pixel_per_mm)))
        blend_width = conf.get("blend_width", 10)

        # 边缘连续性概率配置
        edge_conf = conf.get("edge_continuity", {})
        edge_rib12_prob = edge_conf.get("RIB1-RIB2")
        edge_rib45_prob = edge_conf.get("RIB4-RIB5")

        edge_rib12 = (random.random() < edge_rib12_prob) if edge_rib12_prob is not None else None
        edge_rib45 = (random.random() < edge_rib45_prob) if edge_rib45_prob is not None else None

        continuity_config = {
            "center_mode": continuity_mode,
            "edge_rib12": edge_rib12,
            "edge_rib45": edge_rib45,
        }

        # Step 5: 拼接
        dir_stats = {
            "total_count": 1,
            "processed_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "images": {}
        }

        try:
            debug_dir = str(output_dir / "debug")
            source_names = {"center": center_names, "side": side_names}

            full_image, info = stitch_with_continuity(
                center_images=center_images,
                side_images=side_images,
                continuity_config=continuity_config,
                groove_width_px=groove_width_px,
                blend_width=blend_width,
                debug_dir=debug_dir,
                source_names=source_names,
            )

            # 保存结果图
            output_path = str(output_dir / "tread.png")
            cv2.imwrite(output_path, full_image)

            # 转换 continuity_map: True->"continuous", False->"independent"
            cmap_str = {}
            for k, v in info["continuity_map"].items():
                cmap_str[k] = "continuous" if v else "independent"

            dir_stats["processed_count"] = 1
            dir_stats["success_count"] = 1
            dir_stats["images"]["tread.png"] = {
                "status": "success",
                "output_path": output_path,
                "debug_dir": debug_dir,
                "continuity_map": cmap_str,
                "main_groove_positions": info["main_groove_positions"],
                "actual_rib_widths": info["rib_widths"],
                "image_size": {
                    "width": full_image.shape[1],
                    "height": full_image.shape[0],
                },
                "groove_width_px": groove_width_px,
            }
            logger.info(f"拼接成功: {output_path}")

        except Exception as e:
            dir_stats["processed_count"] = 1
            dir_stats["failed_count"] = 1
            dir_stats["images"]["tread.png"] = {
                "status": "failed",
                "error": str(e),
            }
            logger.error(f"拼接失败: {e}")

        # Step 6: 汇总
        overall_success = dir_stats["success_count"] > 0 and dir_stats["failed_count"] == 0

        result_payload = {
            "task_id": task_id,
            "output_dir": str(output_dir),
            "directories": {output_dir_name: dir_stats},
        }

        if not overall_success:
            err_msg = dir_stats["images"].get("tread.png", {}).get("error", "RIB 连续性拼接失败")
            result_payload["err_msg"] = err_msg
            return False, result_payload

        return True, result_payload

    except Exception as e:
        logger.error(f"Rule 12/16/17 处理异常: {e}")
        return False, {"err_msg": str(e), "task_id": task_id}


# ========== 辅助函数 ==========

def _load_images(image_dir: Path) -> Tuple[List, List[str]]:
    """
    从目录加载所有图像

    Returns:
        (images, file_names) — images 为 BGR ndarray 列表，file_names 为对应文件名列表
    """
    images = []
    names = []
    for f in sorted(image_dir.iterdir()):
        if f.suffix.lower() in _IMAGE_EXTENSIONS:
            img = cv2.imread(str(f))
            if img is not None:
                images.append(img)
                names.append(f.name)
    logger.info(f"从 {image_dir} 加载 {len(images)} 张图像")
    return images, names
