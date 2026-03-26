# -*- coding: utf-8 -*-
"""
rule16_17: RIB横向连续性拼接中间层

功能:
- Rule 16: RIB2/3/4横沟/钢片任意组合连续性
- Rule 17: RIB1/2和RIB4/5可连续可不连续（50%概率）

处理流程:
1. 从 split 目录读取 center_horz 和 side_horz 的 RIB 长条图
2. 按源文件名分组
3. 根据连续性配置调用拼接算法
4. 输出带主沟的完整胎面图

目录关系:
- 输入：.results/task_id_{task_id}/split/center_horz/
         .results/task_id_{task_id}/split/side_horz/
- 输出：.results/task_id_{task_id}/rule16_17/
"""

import cv2
from pathlib import Path
from typing import Dict, List, Tuple, Any

from algorithms.stitching.rib_continuity_stitch import stitch_with_continuity
from utils.logger import get_logger

logger = get_logger("rule16_17")


# ========== 主入口函数 ==========

def process_rib_continuity(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    Rule 16/17 主入口

    参数:
        task_id: 任务ID
        conf: 配置字典
            - base_path: 基础路径（默认 ".results"）
            - input_dir: split 目录名（默认 "split"）
            - continuity_config: 连续性配置
                - center_mode: "RIB2-RIB3" | "RIB3-RIB4" | "RIB2-RIB3-RIB4" | "none"
                - edge_rib12: True/False/None (None=50%随机)
                - edge_rib45: True/False/None (None=50%随机)
            - groove_width_px: 主沟宽度像素（默认20）
            - blend_width: 融合宽度（默认10）
            - output_dir_name: 输出子目录名（默认 "rule16_17"）

    返回:
        (True, {"task_id": ..., "output_dir": ..., "results": {...}})
        或 (False, {"err_msg": ..., "task_id": ...})
    """
    try:
        # Step 1: 路径配置
        base_path = conf.get("base_path", ".results")
        task_dir = Path(base_path) / f"task_id_{task_id}"

        input_dir_name = conf.get("input_dir", "split")
        center_dir = task_dir / input_dir_name / "center_horz"
        side_dir = task_dir / input_dir_name / "side_horz"

        output_dir_name = conf.get("output_dir_name", "rule16_17")
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

        # Step 4: 读取配置
        continuity_config = conf.get("continuity_config", {
            "center_mode": "RIB2-RIB3-RIB4",
            "edge_rib12": None,
            "edge_rib45": None
        })
        groove_width_px = conf.get("groove_width_px", 20)
        blend_width = conf.get("blend_width", 10)
        group_filter = conf.get("group_filter", None)

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
                debug_dir = str(output_dir / f"debug_{group_name}")

                full_image, info = stitch_with_continuity(
                    center_images=center_imgs,
                    side_images=side_imgs,
                    continuity_config=continuity_config,
                    groove_width_px=groove_width_px,
                    blend_width=blend_width,
                    debug_dir=debug_dir,
                    source_names=file_names.get(group_name, {})
                )

                # 保存结果
                output_path = str(output_dir / f"tread_{group_name}.png")
                cv2.imwrite(output_path, full_image)

                dir_stats["processed_count"] += 1
                dir_stats["success_count"] += 1
                dir_stats["images"][f"tread_{group_name}.png"] = {
                    "status": "success",
                    "output_path": output_path,
                    "debug_dir": debug_dir,
                    "continuity_info": info,
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
        summary = {
            "total_images": dir_stats["total_count"],
            "total_processed": dir_stats["processed_count"],
            "total_success": dir_stats["success_count"],
            "total_failed": dir_stats["failed_count"],
            "total_skipped": dir_stats["skipped_count"],
        }

        return True, {
            "task_id": task_id,
            "output_dir": str(output_dir),
            "directories": {"rule16_17": dir_stats},
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"Rule 16/17 处理异常: {e}")
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
