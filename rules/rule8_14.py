# -*- coding: utf-8 -*-
"""
rule8_14: 横沟检测中间层（需求8 & 需求14）

功能:
- 接收 postprocessor 的调用
- 循环 center_inf / side_inf 目录中的所有图片
- 调用 detect_transverse_grooves() 进行检测与评分
- 保存调试标注图和汇总 results.json

目录关系:
- 输入：.results/task_id_{task_id}/center_inf/*.png
        .results/task_id_{task_id}/side_inf/*.png
- 输出：.results/task_id_{task_id}/detect_transverse_grooves/center/
        .results/task_id_{task_id}/detect_transverse_grooves/side/

每张图片输出：
- ``{stem}_debug.png``  : 带标注的调试图
汇总文件：
- ``results.json``      : 所有图片的数值指标列表
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

import cv2

from utils.logger import get_logger

logger = get_logger("rule8_14")

# 输出根目录名（固定，与 gen_report.py 中的 DETECTOR 一致）
_DETECTOR_DIR = "detect_transverse_grooves"

# 默认输入目录列表：目录名 → image_type
_DEFAULT_INPUT_DIRS: Dict[str, str] = {
    "center_inf": "center",
    "side_inf":   "side",
}


# ============================================================
# 主入口
# ============================================================

def process_transverse_grooves(task_id: str, conf: dict) -> Tuple[bool, dict]:
    """
    横沟检测主入口。

    参数
    ----
    task_id : str
        任务 ID（不含 ``task_id_`` 前缀）。
    conf : dict
        配置字典，支持以下键：

        - ``output_base_dir`` (*str*, 默认 ``".results"``): 输出根目录。
        - ``input_dirs`` (*dict*, 可选): 覆盖默认输入目录映射，
          格式 ``{目录名: image_type}``，默认为
          ``{"center_inf": "center", "side_inf": "side"}``。
        - ``groove_width_mm`` (*dict*, 可选): 各类型最小横沟厚度（mm）。
        - ``pixel_per_mm`` (*float*, 可选): 像素密度（px/mm）。
        - ``max_intersections`` (*int*, 可选): 需求14允许的最大交叉点数。

    返回
    ----
    (True, 详细统计字典) 或 (False, {"err_msg": ..., "task_id": ...})
    """
    output_base_dir = conf.get("output_base_dir", ".results")
    task_dir = Path(output_base_dir) / f"task_id_{task_id}"
    input_dirs = conf.get("input_dirs", _DEFAULT_INPUT_DIRS)

    dir_stats: Dict[str, Any] = {}

    for dir_name, image_type in input_dirs.items():
        input_path  = task_dir / dir_name
        output_path = task_dir / _DETECTOR_DIR / image_type

        if not input_path.exists():
            logger.warning("输入目录不存在，跳过：%s", input_path)
            dir_stats[dir_name] = _empty_dir_stats()
            continue

        image_files = _get_image_files(input_path)
        if not image_files:
            logger.warning("目录为空，跳过：%s", input_path)
            dir_stats[dir_name] = _empty_dir_stats()
            continue

        output_path.mkdir(parents=True, exist_ok=True)
        logger.info("处理目录 %s → %s（%d 张图）", dir_name, output_path, len(image_files))

        images_results, images_dict = [], {}
        for fpath in image_files:
            ok, result = _process_single_image(fpath, image_type, output_path, conf)
            images_results.append(result)
            images_dict[fpath.name] = result
            if not ok:
                logger.error("处理失败 %s: %s", fpath.name, result.get("err_msg", "未知错误"))

        # 写 results.json
        _write_results_json(output_path, images_results)

        summary = _aggregate_summary(images_results)
        dir_stats[dir_name] = {
            "total_count":   len(image_files),
            "scored_count":  summary["total_scored"],
            "failed_count":  summary["total_failed"],
            "total_score":   summary["total_score"],
            "images":        images_dict,
        }

    overall = _aggregate_dir_summary(dir_stats)
    return True, {
        "task_id":     task_id,
        "directories": dir_stats,
        "summary":     overall,
    }


# ============================================================
# 单张图片处理
# ============================================================

def _process_single_image(
    fpath: Path,
    image_type: str,
    output_dir: Path,
    conf: dict,
) -> Tuple[bool, Dict[str, Any]]:
    """
    读取图片 → 调用检测函数 → 保存调试图，返回结果字典。
    """
    from algorithms.detection.groove_intersection import detect_transverse_grooves

    try:
        img = cv2.imread(str(fpath))
        if img is None:
            return False, {"file": fpath.name, "status": "failed", "err_msg": "图片读取失败"}

        # 组装检测参数（conf 中未提供的项由函数内部使用 TransverseGroovesConfig 默认值）
        kwargs: Dict[str, Any] = {}
        if "groove_width_mm" in conf:
            kwargs["groove_width_mm"] = conf["groove_width_mm"]
        if "pixel_per_mm" in conf:
            kwargs["pixel_per_mm"] = conf["pixel_per_mm"]
        if "max_intersections" in conf:
            kwargs["max_intersections"] = conf["max_intersections"]

        score, details = detect_transverse_grooves(img, image_type, **kwargs)

        # 保存调试标注图
        debug_fname = f"{fpath.stem}_debug.png"
        cv2.imwrite(str(output_dir / debug_fname), details["debug_image"])

        return True, {
            "file":               fpath.name,
            "status":             "ok",
            "rib_type":           details["rib_type"],
            "groove_count":       details["groove_count"],
            "groove_positions":   details["groove_positions"],
            "intersection_count": details["intersection_count"],
            "is_valid":           details["is_valid"],
            "score_req8":         details["score_req8"],
            "score_req14":        details["score_req14"],
            "total_score":        score,
            "debug_image":        debug_fname,
        }

    except Exception as exc:
        logger.exception("处理图片异常 %s", fpath.name)
        return False, {"file": fpath.name, "status": "failed", "err_msg": str(exc)}


# ============================================================
# 工具函数
# ============================================================

def _get_image_files(directory: Path) -> List[Path]:
    return sorted(
        f for f in directory.iterdir()
        if f.suffix.lower() in (".png", ".jpg", ".jpeg")
    )


def _write_results_json(output_dir: Path, results: List[Dict[str, Any]]) -> None:
    serializable = [
        {k: v for k, v in r.items() if k != "debug_image" or isinstance(v, str)}
        for r in results
    ]
    with open(str(output_dir / "results.json"), "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)


def _empty_dir_stats() -> Dict[str, Any]:
    return {
        "total_count":  0,
        "scored_count": 0,
        "failed_count": 0,
        "total_score":  0,
        "images":       {},
    }


def _aggregate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    scored  = [r for r in results if r.get("status") == "ok"]
    failed  = [r for r in results if r.get("status") != "ok"]
    return {
        "total_images":  len(results),
        "total_scored":  len(scored),
        "total_failed":  len(failed),
        "total_score":   sum(r.get("total_score", 0) for r in scored),
    }


def _aggregate_dir_summary(dir_stats: Dict[str, Any]) -> Dict[str, Any]:
    total_images  = sum(s["total_count"]  for s in dir_stats.values())
    total_scored  = sum(s["scored_count"] for s in dir_stats.values())
    total_failed  = sum(s["failed_count"] for s in dir_stats.values())
    total_score   = sum(s["total_score"]  for s in dir_stats.values())
    return {
        "total_images": total_images,
        "total_scored": total_scored,
        "total_failed": total_failed,
        "total_score":  total_score,
    }
