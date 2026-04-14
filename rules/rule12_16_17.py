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
from algorithms.stitching.rib_continuity_stitch import (
    detect_main_grooves,
    split_image_to_ribs,
    reassemble_ribs_with_continuity,
)
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

            # 构建输出文件名: tread_center-{stems}_side-{stems}_{mode}.png
            center_stems = "-".join(Path(n).stem for n in center_names)
            side_stems = "-".join(Path(n).stem for n in side_names)
            output_filename = f"tread_center-{center_stems}_side-{side_stems}_{continuity_mode}.png"
            output_path = str(output_dir / output_filename)
            if not cv2.imwrite(output_path, full_image):
                raise RuntimeError(f"cv2.imwrite 写入失败: {output_path}")

            # 转换 continuity_map: True->"continuous", False->"independent"
            cmap_str = {}
            for k, v in info["continuity_map"].items():
                cmap_str[k] = "continuous" if v else "independent"

            dir_stats["processed_count"] = 1
            dir_stats["success_count"] = 1
            dir_stats["images"][output_filename] = {
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


# ========== 从横图拼接结果进行 RIB 连续性处理 ==========

def process_rib_continuity_from_horizontal(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    从横图拼接结果切分 RIB 并按连续性配置重新拼接

    流程:
    1. 读取 input_dir（横图拼接输出）下所有图片
    2. 对每张图检测主沟位置，切分为 rib1~rib5
    3. 按 continuity_config 调用 reassemble_ribs_with_continuity 重新拼接
    4. 保存到 output_dir

    参数:
        task_id: 任务ID
        conf: 配置字典
            - base_path: 基础路径（默认 ".results"）
            - input_dir: 横图拼接输出子目录（默认 "combine_horizontal"）
            - output_dir: 输出子目录名（默认 "rib_continuity"）
            - continuity_mode: "RIB2-RIB3" | "RIB3-RIB4" | "RIB2-RIB3-RIB4" | "none"
            - groove_width_mm: 主沟宽度(mm)，默认10.0
            - pixel_per_mm: 像素/毫米，默认2.0
            - blend_width: 融合宽度像素（默认10）
            - edge_continuity: 边缘连续性概率配置
                - "RIB1-RIB2": 0.0~1.0 概率
                - "RIB4-RIB5": 0.0~1.0 概率

    返回:
        (True, {"task_id": ..., "directories": {...}, "summary": {...}})
        或 (False, {"err_msg": ..., "task_id": ...})
    """
    try:
        # Step 1: 路径配置
        base_path = conf.get("base_path", ".results")
        task_dir = Path(base_path) / f"task_id_{task_id}"

        input_dir_name = conf.get("input_dir", "combine_horizontal")
        input_dir = task_dir / input_dir_name

        output_dir_name = conf.get("output_dir", "rib_continuity")
        output_dir = task_dir / output_dir_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 2: 校验输入目录
        if not input_dir.exists():
            return False, {"err_msg": f"横图拼接输出目录不存在: {input_dir}", "task_id": task_id}

        # Step 3: 加载所有横图拼接结果
        images_with_names = _load_images(input_dir)
        all_images, all_names = images_with_names

        if not all_images:
            return False, {"err_msg": f"横图拼接输出目录无图片: {input_dir}", "task_id": task_id}

        # Step 4: 解析连续性配置
        continuity_mode = conf.get("continuity_mode", "none")
        groove_width_mm = conf.get("groove_width_mm", 10.0)
        pixel_per_mm = conf.get("pixel_per_mm", 2.0)
        groove_width_px = max(1, int(round(groove_width_mm * pixel_per_mm)))
        blend_width = conf.get("blend_width", 10)

        edge_conf = conf.get("edge_continuity", {})
        edge_rib12_prob = edge_conf.get("RIB1-RIB2")
        edge_rib45_prob = edge_conf.get("RIB4-RIB5")

        # Step 5: 逐张处理
        dir_stats = {
            "total_count": len(all_images),
            "processed_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "images": {}
        }

        for img, name in zip(all_images, all_names):
            stem = Path(name).stem
            dir_stats["processed_count"] += 1

            try:
                # 5a: 检测主沟
                groove_regions = detect_main_grooves(
                    img, min_groove_width=groove_width_px // 2, threshold=30
                )

                # 5b: 切分为 rib1~rib5
                ribs = split_image_to_ribs(img, groove_regions)

                # 5c: 每张图独立计算边缘连续性概率
                edge_rib12 = (random.random() < edge_rib12_prob) if edge_rib12_prob is not None else None
                edge_rib45 = (random.random() < edge_rib45_prob) if edge_rib45_prob is not None else None

                continuity_config = {
                    "center_mode": continuity_mode,
                    "edge_rib12": edge_rib12,
                    "edge_rib45": edge_rib45,
                }

                # 5d: 调试目录
                debug_subdir = str(output_dir / "debug" / stem) if conf.get("debug", False) else None

                # 5e: 重新拼接
                full_image, info = reassemble_ribs_with_continuity(
                    ribs=ribs,
                    continuity_config=continuity_config,
                    groove_width_px=groove_width_px,
                    blend_width=blend_width,
                    debug_dir=debug_subdir,
                )

                # 5f: 保存结果
                output_filename = f"{stem}_{continuity_mode}.png"
                output_path = str(output_dir / output_filename)
                if not cv2.imwrite(output_path, full_image):
                    raise RuntimeError(f"cv2.imwrite 写入失败: {output_path}")

                # 转换 continuity_map
                cmap_str = {
                    k: "continuous" if v else "independent"
                    for k, v in info["continuity_map"].items()
                }

                dir_stats["success_count"] += 1
                dir_stats["images"][output_filename] = {
                    "status": "success",
                    "output_path": output_path,
                    "source": name,
                    "continuity_map": cmap_str,
                    "main_groove_positions": info["main_groove_positions"],
                    "actual_rib_widths": info["rib_widths"],
                    "image_size": {
                        "width": full_image.shape[1],
                        "height": full_image.shape[0],
                    },
                    "groove_width_px": groove_width_px,
                }
                logger.info(f"rib continuity 成功: {name} -> {output_filename}")

            except Exception as e:
                dir_stats["failed_count"] += 1
                dir_stats["images"][name] = {
                    "status": "failed",
                    "error": str(e),
                }
                logger.error(f"rib continuity 处理失败 [{name}]: {e}")

        # Step 6: 汇总
        summary = {
            "total_images": dir_stats["total_count"],
            "total_processed": dir_stats["processed_count"],
            "total_success": dir_stats["success_count"],
            "total_failed": dir_stats["failed_count"],
            "total_skipped": dir_stats["skipped_count"],
        }

        overall_success = dir_stats["success_count"] > 0 and dir_stats["failed_count"] == 0
        result_payload = {
            "task_id": task_id,
            "output_dir": str(output_dir),
            "directories": {output_dir_name: dir_stats},
            "summary": summary,
        }

        if not overall_success:
            failed_imgs = [k for k, v in dir_stats["images"].items() if v.get("status") == "failed"]
            err_msg = f"RIB连续性处理失败: {failed_imgs}"
            result_payload["err_msg"] = err_msg
            return False, result_payload

        return True, result_payload

    except Exception as e:
        logger.error(f"process_rib_continuity_from_horizontal 异常: {e}")
        return False, {"err_msg": str(e), "task_id": task_id}


# ========== 辅助函数 ==========

def _numeric_sort_key(p: Path):
    """数字感知排序键：stem 能转为整数时按数值排序，否则按文件名字符串排序"""
    try:
        return (0, int(p.stem), p.name)
    except ValueError:
        return (1, 0, p.name)


def _load_images(image_dir: Path) -> Tuple[List, List[str]]:
    """
    从目录加载所有图像

    Returns:
        (images, file_names) — images 为 BGR ndarray 列表，file_names 为对应文件名列表
    """
    candidates = sorted(
        (f for f in image_dir.iterdir() if f.is_file() and f.suffix.lower() in _IMAGE_EXTENSIONS),
        key=_numeric_sort_key,
    )
    images = []
    names = []
    for f in candidates:
        img = cv2.imread(str(f))
        if img is not None:
            images.append(img)
            names.append(f.name)
    logger.info(f"从 {image_dir} 加载 {len(images)} 张图像")
    return images, names
