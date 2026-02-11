# main.py
import os
import json
import cv2
import numpy as np

from read_data import list_images, read_image_bgr
from data_operation.crop_tdw import detect_centerline_x
from function.land_sea_ratio import compute_land_sea_ratio, filter_by_land_sea_ratio
from function.symmetry_check import symmetry_score_mirror, symmetry_pass

def to_percent(x: float) -> str:
    return f"{x * 100:.2f}%"

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def draw_visualization(original_bgr,
                       tdw_bgr,
                       center_x_tdw: int,
                       land_mask,
                       sym_best_shift: int,
                       save_path: str):
    """
    输出可视化：
    - 原图（就是TDW）
    - TDW中心线
    - TDW花纹mask预览
    """
    # 原图可视化
    vis = original_bgr.copy()
    H0, W0 = vis.shape[:2]
    cv2.putText(vis, "INPUT(TDW)", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

    # TDW可视化
    tdw_vis = tdw_bgr.copy()
    H, W = tdw_vis.shape[:2]

    # 中心线
    cx = int(center_x_tdw)
    cv2.line(tdw_vis, (cx, 0), (cx, H - 1), (0, 0, 255), 2)
    cv2.putText(tdw_vis, f"center_x={cx}", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # shift信息
    cv2.putText(tdw_vis, f"best_shift={sym_best_shift}", (10, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    # mask可视化
    mask_vis = cv2.cvtColor(land_mask, cv2.COLOR_GRAY2BGR)

    # 拼图输出（统一高度）
    tdw_h = tdw_vis.shape[0]

    scale = tdw_h / vis.shape[0]
    vis_small = cv2.resize(vis, (int(vis.shape[1] * scale), tdw_h))

    out = np.hstack([vis_small, tdw_vis, mask_vis])
    cv2.imwrite(save_path, out)


def run_one_image(img_path: str,
                  output_visual_dir: str,
                  config: dict):
    """
    单张图处理（整张图就是TDW）
    """
    name, img_bgr = read_image_bgr(img_path)

    tdw_bgr = img_bgr  # ⭐关键：整张图直接作为TDW

    # 1) 中心线检测
    center_x = detect_centerline_x(tdw_bgr)

    # 2) 海陆比
    land_res = compute_land_sea_ratio(
        tdw_bgr,
        use_otsu=config["land_sea"]["use_otsu"],
        fixed_thr=config["land_sea"]["fixed_thr"],
        blur_ksize=config["land_sea"]["blur_ksize"],
        morph_open=config["land_sea"]["morph_open"]
    )
    land_ratio = land_res["land_sea_ratio"]
    land_filter = filter_by_land_sea_ratio(
        land_ratio,
        low=config["land_sea"]["low"],
        high=config["land_sea"]["high"]
    )

    # 3) 对称性
    sym_res = symmetry_score_mirror(
        tdw_bgr,
        center_x=center_x,
        allow_shift_px=config["symmetry"]["allow_shift_px"]
    )
    sym_score = sym_res["best_score"]
    sym_filter = symmetry_pass(sym_score, threshold=config["symmetry"]["threshold"])

    # 4) passed数组
    passed_array = [
        bool(land_filter["passed"]),
        bool(sym_filter["passed"])
    ]

    # 5) 可视化输出
    ensure_dir(output_visual_dir)
    vis_path = os.path.join(output_visual_dir, f"{os.path.splitext(name)[0]}_vis.jpg")

    draw_visualization(
        original_bgr=img_bgr,
        tdw_bgr=tdw_bgr,
        center_x_tdw=center_x,
        land_mask=land_res["mask_land"],
        sym_best_shift=sym_res["best_shift"],
        save_path=vis_path
    )

    return {
        "file_name": name,
        "file_path": img_path,

        # 整图只有1个TDW
        "tdw_count": 1,

        # 统一输出结构：tdw_results列表
        "tdw_results": [
            {
                "tdw_index": 0,
                "passed": passed_array,

                # 这里不再有裁剪框，整图就是TDW
                "tdw_crop": {
                    "crop_box_xyxy": (0, 0, int(img_bgr.shape[1]), int(img_bgr.shape[0])),
                    "tdw_size": (int(img_bgr.shape[1]), int(img_bgr.shape[0]))
                },

                "land_sea": {
                    "ratio": land_ratio,
                    "passed": land_filter["passed"],
                    "threshold_low": land_filter["threshold_low"],
                    "threshold_high": land_filter["threshold_high"]
                },

                "symmetry": {
                    "score": sym_score,
                    "passed": sym_filter["passed"],
                    "threshold": sym_filter["threshold"],
                    "center_x": int(center_x),
                    "best_shift": int(sym_res["best_shift"]),
                    "allow_shift_px": int(sym_res["allow_shift_px"])
                },

                "visual_path": vis_path
            }
        ]
    }


def main():
    # =========================
    # 配置项
    # =========================
    config = {
        "land_sea": {
            "use_otsu": True,
            "fixed_thr": 240,
            "blur_ksize": 3,
            "morph_open": True,
            "low": 0.20,
            "high": 0.50
        },
        "symmetry": {
            "allow_shift_px": 20,
            "threshold": 0.90
        }
    }

    # =========================
    # 输入路径：支持文件或文件夹
    # =========================
    input_path = "./input/combine_result/combined_result_tile2.jpg"
    input_path = "./input/combine_result/"

    # =========================
    # 输出路径
    # =========================
    output_dir = "output/"
    output_visual_dir = os.path.join(output_dir, "image_handl/")
    ensure_dir(output_dir)
    ensure_dir(output_visual_dir)

    img_list = list_images(input_path)
    if not img_list:
        raise RuntimeError(f"未找到图片: {input_path}")

    results = []
    for i, img_path in enumerate(img_list, start=1):
        try:
            print(f"[{i}/{len(img_list)}] Processing: {img_path}")
            res = run_one_image(img_path, output_visual_dir, config)
            results.append(res)
        except Exception as e:
            results.append({
                "file_name": os.path.basename(img_path),
                "file_path": img_path,
                "passed": False,
                "error": str(e)
            })
            print(f"  -> ERROR: {e}")

    # 保存json
    json_path = os.path.join(output_dir, "results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n***********************************")
    print(f"Total_images: {len(results)}")
    print("===================================")

    for res in results:
        print(f"File: {res['file_name']}")

        if "error" in res:
            print(f"  ERROR: {res['error']}")
            print("===================================")
            continue

        tdw_res = res["tdw_results"][0]

        land_ratio = tdw_res["land_sea"]["ratio"]          # 0~1
        sym_score = tdw_res["symmetry"]["score"]           # 0~1

        print(f"  Land-Sea Ratio: {to_percent(land_ratio)}")
        print(f"  Symmetry SSIM : {to_percent(sym_score)}")
        print("===================================")

    print(f"JSON saved: {json_path}")
    print(f"Visual saved: {output_visual_dir}")
    print("***********************************\n")


if __name__ == "__main__":
    main()
