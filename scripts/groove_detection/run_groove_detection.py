"""
纵向细沟检测命令行脚本
=====================

用法::

    python scripts/run_groove_detection.py <image_path> [--type center|side]
                                            [--groove-width 0.34] [--ppm 11.81]
                                            [--save-debug <output_path>]

输出（stdout）::

    count=<N>
    score=<S>

示例::

    python scripts/run_groove_detection.py tests/datasets/task_id_1778457600/images/center.png
    python scripts/run_groove_detection.py side.png --type side --save-debug debug_out.png
"""

import argparse
import pathlib
import sys

# 确保项目根目录在路径中（无论从何处调用脚本）
_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="检测轮胎小图中的纵向细沟数量与评分",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("image", help="输入图像路径（BGR，典型尺寸 128×128）")
    parser.add_argument(
        "--type",
        dest="image_type",
        default="center",
        choices=["center", "side"],
        help="小图类型：center（RIB2/3/4）或 side（RIB1/5）",
    )
    parser.add_argument(
        "--groove-width",
        type=float,
        default=0.34,
        metavar="MM",
        help="纵向线条名义宽度（mm）",
    )
    parser.add_argument(
        "--ppm",
        type=float,
        default=11.81,
        metavar="PX/MM",
        help="像素密度（px/mm）",
    )
    parser.add_argument(
        "--save-debug",
        metavar="OUTPUT_PATH",
        default=None,
        help="保存含标注信息的调试图像（可选）",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # 延迟导入——避免 sys.path 操作前加载
    try:
        import cv2
    except ImportError:
        print("ERROR: 需要安装 opencv-python（pip install opencv-python）", file=sys.stderr)
        sys.exit(1)

    from algorithms.detection.longitudinal_groove import detect_longitudinal_grooves

    # ── 读取图像 ──────────────────────────────────────────────────
    img_path = pathlib.Path(args.image)
    if not img_path.exists():
        print(f"ERROR: 文件不存在：{img_path}", file=sys.stderr)
        sys.exit(1)

    img = cv2.imread(str(img_path))
    if img is None:
        print(f"ERROR: 无法读取图像（格式不支持或文件损坏）：{img_path}", file=sys.stderr)
        sys.exit(1)

    # ── 执行检测 ──────────────────────────────────────────────────
    score, details = detect_longitudinal_grooves(
        img,
        args.image_type,
        groove_width_mm=args.groove_width,
        pixel_per_mm=args.ppm,
    )

    if score is None:
        print(f"ERROR: 检测失败——{details.get('err_msg', '未知错误')}", file=sys.stderr)
        sys.exit(1)

    # ── 输出结果 ──────────────────────────────────────────────────
    print(f"count={details['groove_count']}")
    print(f"score={score:.1f}")

    # ── 可选：保存调试图 ──────────────────────────────────────────
    if args.save_debug:
        debug_img = details.get("debug_image")
        if debug_img is not None:
            out_path = pathlib.Path(args.save_debug)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out_path), debug_img)
            print(f"debug_image={out_path}")
        else:
            print("WARN: 调试图像不可用", file=sys.stderr)


if __name__ == "__main__":
    main()
