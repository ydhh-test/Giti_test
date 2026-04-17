# -*- coding: utf-8 -*-
"""
纵向细沟 & 纵向钢片检测可视化脚本

读取 tests/datasets/task_longitudinal_groove_vis 下的 center_inf / side_inf 小图，
对每张图运行 detect_longitudinal_grooves，将可视化结果（debug_image）保存到
.results/task_longitudinal_groove_vis/<image_type>/<stem>_debug.png。

同时在控制台打印每张图的检测结果（得分、纵沟数量、位置、宽度）。
"""

import sys
import pathlib

# 确保项目根目录在 sys.path 中
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import cv2
import numpy as np
from algorithms.detection.longitudinal_groove import detect_longitudinal_grooves

# ─── 路径配置 ───────────────────────────────────────────
TASK_ID      = "task_longitudinal_groove_vis"
DATASETS_DIR = _ROOT / "tests" / "datasets" / TASK_ID
RESULTS_DIR  = _ROOT / ".results" / TASK_ID

# center_inf → image_type="center"；side_inf → image_type="side"
TYPE_MAP = {
    "center_inf": "center",
    "side_inf":   "side",
}

# ─── 主逻辑 ─────────────────────────────────────────────
def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for sub_dir, image_type in TYPE_MAP.items():
        src_dir = DATASETS_DIR / sub_dir
        if not src_dir.exists():
            print(f"[SKIP] 目录不存在: {src_dir}")
            continue

        out_dir = RESULTS_DIR / sub_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        imgs = sorted(src_dir.glob("*.png")) + sorted(src_dir.glob("*.jpg"))
        if not imgs:
            print(f"[SKIP] {src_dir} 下无图片")
            continue

        print(f"\n{'='*60}")
        print(f"[{image_type.upper()}]  {src_dir}  →  {out_dir}")
        print(f"{'='*60}")

        for img_path in imgs:
            bgr = cv2.imread(str(img_path))
            if bgr is None:
                print(f"  [ERR]  无法读取: {img_path.name}")
                continue

            score, details = detect_longitudinal_grooves(bgr, image_type)

            if score is None:
                print(f"  [ERR]  {img_path.name}: {details.get('err_msg')}")
                continue

            # ── 打印结果 ──
            count    = details["groove_count"]
            valid    = details["is_valid"]
            positions= details["groove_positions"]
            widths   = details["groove_widths"]
            rib_type = details["rib_type"]
            status   = "PASS" if valid else "FAIL"

            print(
                f"  [{status}]  {img_path.name:<12}  "
                f"score={score:.0f}  count={count}  "
                f"rib={rib_type}  "
                f"pos={[round(p,1) for p in positions]}  "
                f"widths={[round(w,1) for w in widths]}"
            )

            # ── 保存 debug_image ──
            debug_img  = details.get("debug_image")
            line_mask  = details.get("line_mask")

            # 在 debug_image 左上角叠加文字标注
            if debug_img is not None:
                label = f"score={score:.0f} | count={count} | {status}"
                cv2.putText(
                    debug_img, label,
                    (4, 14), cv2.FONT_HERSHEY_SIMPLEX,
                    0.38, (0, 200, 255), 1, cv2.LINE_AA
                )
                out_path = out_dir / f"{img_path.stem}_debug.png"
                cv2.imwrite(str(out_path), debug_img)
                print(f"           → 保存: {out_path.relative_to(_ROOT)}")

            # 可选：也保存 line_mask
            if line_mask is not None:
                mask_path = out_dir / f"{img_path.stem}_mask.png"
                cv2.imwrite(str(mask_path), line_mask)

    print(f"\n完成。结果目录: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
