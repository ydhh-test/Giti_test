# -*- coding: utf-8 -*-
"""
rule12_16_17: RIB横向连续性拼接中间层

功能:
- Rule 16: RIB2/3/4横沟/钢片任意组合连续性
- Rule 17: RIB1/2和RIB4/5可连续可不连续（概率控制）

处理流程:
1. 从 split 目录读取 center_horz 和 side_horz 的 RIB 长条图
2. 按源文件名分组
3. 根据连续性配置调用拼接算法
4. 输出带主沟的完整胎面图

目录关系:
- 输入：.results/task_id_{task_id}/split/center_horz/
         .results/task_id_{task_id}/split/side_horz/
- 输出：.results/task_id_{task_id}/{output_dir}/
"""

import cv2
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any

from algorithms.stitching.rib_continuity_stitch import stitch_with_continuity
from utils.logger import get_logger

logger = get_logger("rule12_16_17")


# ========== 主入口函数 ==========

def process_rib_continuity(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    Rule 12/16/17 主入口

    参数:
        task_id: 任务ID
        conf: 配置字典
            - base_path: 基础路径（默认 ".results"）
            - input_dir: split 目录名（默认 "split"）
            - continuity_mode: "RIB2-RIB3" | "RIB3-RIB4" | "RIB2-RIB3-RIB4" | "none"
            - groove_width_mm: 主沟宽度(mm)，默认10.0
            - pixel_per_mm: 像素/毫米，默认2.0
            - blend_width: 融合宽度像素（默认10）
            - edge_continuity: 边缘连续性概率配置
                - "RIB1-RIB2": 0.0~1.0 概率
                - "RIB4-RIB5": 0.0~1.0 概率
            - output_dir: 输出子目录名（默认 "rule12_16_17"）
            - group_filter: 可选分组名过滤列表

    返回:
        (True, {"task_id": ..., "output_dir": ..., "directories": {...}})
        或 (False, {"err_msg": ..., "task_id": ...})
    """
    try:
        # Step 1: 路径配置
        base_path = conf.get("base_path", ".results")
        task_dir = Path(base_path) / f"task_id_{task_id}"

        input_dir_name = conf.get("input_dir", "split")
        center_dir = task_dir / input_dir_name / "center_horz"
        side_dir = task_dir / input_dir_name / "side_horz"

        output_dir_name = conf.get("output_dir", "rule12_16_17")
        output_dir = task_dir / output_dir_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 2: 校验输入
        if not center_dir.exists():
            return False, {"err_msg": f"center目录不存在: {center_dir}", "task_id": task_id}
        if not side_dir.exists():
            return False, {"err_msg": f"side目录不存在: {side_dir}", "task_id": task_id}

        # Step 3: 加载并分组图像
        center_groups, side_groups, file_names = _load_and_group_images(center_dir, side_dir)

        if not center_groups:
            return False, {"err_msg": "未找到center RIB图像", "task_id": task_id}

        # Step 4: 解析配置
        continuity_mode = conf.get("continuity_mode", "none")
        groove_width_mm = conf.get("groove_width_mm", 10.0)
        pixel_per_mm = conf.get("pixel_per_mm", 2.0)
        groove_width_px = max(1, int(round(groove_width_mm * pixel_per_mm)))
        blend_width = conf.get("blend_width", 10)
        group_filter = conf.get("group_filter", None)

        # 边缘连续性概率配置（每组独立采样）
        edge_conf = conf.get("edge_continuity", {})
        edge_rib12_prob = edge_conf.get("RIB1-RIB2")
        edge_rib45_prob = edge_conf.get("RIB4-RIB5")

        # Step 5: 处理每组图像
        dir_stats = {
            "total_count": 0,
            "processed_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "images": {}
        }

        for group_name, center_imgs in center_groups.items():
            if group_filter and group_name not in group_filter:
                logger.info(f"组 {group_name} 不在 group_filter 中，跳过")
                dir_stats["skipped_count"] += 1
                continue

            side_imgs = side_groups.get(group_name, [])
            if not side_imgs:
                logger.warning(f"组 {group_name} 缺少side图像，跳过")
                dir_stats["skipped_count"] += 1
                continue

            dir_stats["total_count"] += 1

            try:
                # 每组独立按概率采样边缘连续性
                edge_rib12 = (random.random() < edge_rib12_prob) if edge_rib12_prob is not None else None
                edge_rib45 = (random.random() < edge_rib45_prob) if edge_rib45_prob is not None else None
                continuity_config = {
                    "center_mode": continuity_mode,
                    "edge_rib12": edge_rib12,
                    "edge_rib45": edge_rib45,
                }

                group_debug_dir = str(output_dir / f"debug_{group_name}")

                full_image, info = stitch_with_continuity(
                    center_images=center_imgs,
                    side_images=side_imgs,
                    continuity_config=continuity_config,
                    groove_width_px=groove_width_px,
                    blend_width=blend_width,
                    debug_dir=group_debug_dir,
                    source_names=file_names.get(group_name, {})
                )

                # 保存结果图
                output_path = str(output_dir / f"tread_{group_name}.png")
                cv2.imwrite(output_path, full_image)

                # 转换 continuity_map: True->"continuous", False->"independent"
                cmap_str = {}
                for k, v in info["continuity_map"].items():
                    cmap_str[k] = "continuous" if v else "independent"

                dir_stats["processed_count"] += 1
                dir_stats["success_count"] += 1
                dir_stats["images"][f"tread_{group_name}.png"] = {
                    "status": "success",
                    "output_path": output_path,
                    "debug_dir": group_debug_dir,
                    "continuity_map": cmap_str,
                    "main_groove_positions": info["main_groove_positions"],
                    "actual_rib_widths": info["rib_widths"],
                    "image_size": {
                        "width": full_image.shape[1],
                        "height": full_image.shape[0],
                    },
                    "groove_width_px": groove_width_px,
                }
                logger.info(f"组 {group_name} 拼接成功: {output_path}")

            except Exception as e:
                dir_stats["processed_count"] += 1
                dir_stats["failed_count"] += 1
                dir_stats["images"][f"tread_{group_name}.png"] = {
                    "status": "failed",
                    "error": str(e),
                }
                logger.error(f"组 {group_name} 拼接失败: {e}")

        # Step 6: 汇总
        success_count = dir_stats["success_count"]
        failed_count = dir_stats["failed_count"]
        processed_count = dir_stats["processed_count"]
        total_count = dir_stats["total_count"]
        skipped_count = dir_stats["skipped_count"]

        overall_success = success_count > 0 and failed_count == 0

        result_payload = {
            "task_id": task_id,
            "output_dir": str(output_dir),
            "directories": {output_dir_name: dir_stats},
        }

        if not overall_success:
            if processed_count == 0 and total_count == 0 and skipped_count > 0:
                err_msg = "所有分组均被跳过，未进行任何拼接"
            elif success_count == 0 and failed_count > 0:
                err_msg = f"所有分组拼接失败：failed_count={failed_count}"
            elif failed_count > 0:
                err_msg = (
                    f"部分分组拼接失败：success_count={success_count}, "
                    f"failed_count={failed_count}"
                )
            else:
                err_msg = "RIB 连续性拼接失败，统计结果异常"

            result_payload["err_msg"] = err_msg
            return False, result_payload

        return True, result_payload

    except Exception as e:
        logger.error(f"Rule 12/16/17 处理异常: {e}")
        return False, {"err_msg": str(e), "task_id": task_id}


# ========== 辅助函数 ==========

def _load_and_group_images(
    center_dir: Path, side_dir: Path
) -> Tuple[Dict[str, list], Dict[str, list], Dict[str, dict]]:
    """
    加载图像并按文件名前缀分组

    文件名格式: {source}_{source}_part{N}_split.png
    分组依据: part 之前的前缀

    Returns:
        (center_groups, side_groups, file_names_map)
    """
    extensions = {'.png', '.jpg', '.jpeg', '.bmp'}

    def get_group_key(filename: str) -> str:
        """提取分组键：_part 之前的全部内容"""
        idx = filename.rfind('_part')
        if idx > 0:
            return filename[:idx]
        return filename.rsplit('.', 1)[0]

    center_groups: Dict[str, list] = {}
    side_groups: Dict[str, list] = {}
    file_names: Dict[str, dict] = {}

    # 加载 center
    for f in sorted(center_dir.iterdir()):
        if f.suffix.lower() in extensions:
            img = cv2.imread(str(f))
            if img is not None:
                key = get_group_key(f.name)
                center_groups.setdefault(key, []).append(img)
                file_names.setdefault(key, {"center": [], "side": []})
                file_names[key]["center"].append(f.name)

    # 加载 side
    for f in sorted(side_dir.iterdir()):
        if f.suffix.lower() in extensions:
            img = cv2.imread(str(f))
            if img is not None:
                key = get_group_key(f.name)
                side_groups.setdefault(key, []).append(img)
                file_names.setdefault(key, {"center": [], "side": []})
                file_names[key]["side"].append(f.name)

    logger.info(f"加载图像分组: {list(center_groups.keys())}, center组数={len(center_groups)}, side组数={len(side_groups)}")
    return center_groups, side_groups, file_names
