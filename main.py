# main.py
import os
import json
import cv2
import numpy as np

from read_data import list_images, read_image_bgr
from crop_tdw import crop_tdw_region, detect_centerline_x
from land_sea_ratio import compute_land_sea_ratio, filter_by_land_sea_ratio
from symmetry_check import symmetry_score_mirror, symmetry_pass


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def draw_visualization(original_bgr,
                       crop_info,
                       tdw_bgr,
                       center_x_tdw: int,
                       land_mask,
                       sym_best_shift: int,
                       save_path: str):
    """
    输出可视化：
    - 原图裁剪框
    - TDW图中心线
    - TDW花纹mask预览
    """
    vis = original_bgr.copy()
    x1, y1, x2, y2 = crop_info["crop_box_xyxy"]
    cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.putText(vis, "TDW", (x1, max(20, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

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

    # 拼图输出
    # 原图缩放到和TDW高度一致
    tdw_h = tdw_vis.shape[0]
    scale = tdw_h / vis.shape[0]
    vis_small = cv2.resize(vis, (int(vis.shape[1] * scale), tdw_h))

    out = np.hstack([vis_small, tdw_vis, mask_vis])
    cv2.imwrite(save_path, out)


def run_one_image(img_path: str,
                  output_visual_dir: str,
                  config: dict):
    """
    单张图处理，返回结果dict
    """
    name, img_bgr = read_image_bgr(img_path)

    # 1) 裁剪TDW
    tdw_bgr, crop_info = crop_tdw_region(
        img_bgr,
        padding=config["crop"]["padding"],
        min_area_ratio=config["crop"]["min_area_ratio"]
    )

    # 2) 中心线检测
    center_x = detect_centerline_x(tdw_bgr)

    # 3) 海陆比
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

    # 4) 对称性
    sym_res = symmetry_score_mirror(
        tdw_bgr,
        center_x=center_x,
        allow_shift_px=config["symmetry"]["allow_shift_px"]
    )
    sym_score = sym_res["best_score"]
    sym_filter = symmetry_pass(sym_score, threshold=config["symmetry"]["threshold"])

    # 5) 通过
    # passed1 = bool(land_filter["passed"])
    # passed2=bool(sym_filter["passed"])
    passed_array = [
    bool(land_filter["passed"]),  # 第1项：海陆比
    bool(sym_filter["passed"])    # 第2项：对称性
]


    # 6) 可视化输出
    ensure_dir(output_visual_dir)
    vis_path = os.path.join(output_visual_dir, f"{os.path.splitext(name)[0]}_vis.jpg")
    draw_visualization(
        original_bgr=img_bgr,
        crop_info=crop_info,
        tdw_bgr=tdw_bgr,
        center_x_tdw=center_x,
        land_mask=land_res["mask_land"],
        sym_best_shift=sym_res["best_shift"],
        save_path=vis_path
    )

    result = {
        "file_name": name,
        "file_path": img_path,

        "passed": passed_array,

        "tdw_crop": {
            "crop_box_xyxy": crop_info["crop_box_xyxy"],
            "tdw_size": crop_info["tdw_size"]
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
    return result


def main():
    # =========================
    # 你可以改的配置项（非常重要）
    # =========================
    config = {
        "crop": {
            "padding": 10,
            "min_area_ratio": 0.05
        },
        "land_sea": {
            "use_otsu": True,
            "fixed_thr": 240,
            "blur_ksize": 3,
            "morph_open": True,
            "low": 0.20,
            "high": 0.50
        },
        "symmetry": {
            # 细则3：严格镜像对称
            # 细则4：允许错位（例如 20）
            "allow_shift_px": 20,
            "threshold": 0.90
        }
    }

    # =========================
    # 输入路径：支持文件或文件夹
    # =========================
    input_path = "./input/combine_result"  # 可以改成你的图片文件夹或单张图片路径

    # =========================
    # 输出路径
    # =========================
    output_dir = "output"
    output_visual_dir = os.path.join(output_dir, "visual/combine_result")
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
            # 单张失败不影响全局
            results.append({
                "file_name": os.path.basename(img_path),
                "file_path": img_path,
                "passed": False,
                "error": str(e)
            })
            print(f"  -> ERROR: {e}")

    # 保存json
    json_path = os.path.join(output_dir, "results_conbine.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 打印汇总
    # passed_count = sum(1 for r in results if r.get("passed") is True)
    # passed_count = sum(passed)
    # failed_count = len(passed) - sum(passed)

    total_passed = 0
    total_failed = 0
    # for res in results:
    #     passed_arr = res.get("passed", [])
    #     total_passed += sum(passed_arr)
    #     total_failed += len(passed_arr) - sum(passed_arr)

    print("\n***********************************")
    print(f"Total_image: {len(results)}") #总图片数
    print("===================================")
    for res in results: #打印每一个图片的结果
        print(f"File: {res['file_name']}")
        passed_arr = res.get("passed", [])

        if isinstance(passed_arr, bool):
            passed_arr = [passed_arr]

        passed_count = sum(passed_arr)
        failed_count = len(passed_arr) - sum(passed_arr)

        total_passed += passed_count
        total_failed += failed_count

        print(f"Passed_item: {passed_count}")
        print(f"Failed_item: {failed_count}")
        print("===================================")

    print(f"Total_passed: {total_passed}")
    print(f"Total_failed: {total_failed}")
    print(f"JSON saved: {json_path}")
    print(f"Visual saved: {output_visual_dir}")
    print("***********************************\n")


if __name__ == "__main__":
    main()
