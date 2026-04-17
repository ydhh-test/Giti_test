# -*- coding: utf-8 -*-
"""
生成纵向细沟检测算法的合成测试图像。

在 tests/datasets/task_longitudinal_groove_vis/center_inf 和 side_inf 目录下
生成一批包含随机纵向细沟的 128×128 BGR 测试图像，命名规范：
    syn_<场景描述>_<编号>.png

图像模拟真实轮胎小图的视觉特征：
- 背景：浅灰（185±15）+ 轻微纹理噪声，模拟橡胶花纹块
- 纵向细沟：深灰暗带（25-50），宽度 3-5px（≈±50% 容差内，名义约 4px），
  在垂直方向覆盖 80-100% 图高（真实纵沟），交替明暗行模拟真实纹理
- 倾斜纵沟：25° 倾斜（通过，<30°）和 35° 倾斜（拒绝，>30°）
- 分离短段：三段错位短暗带，验证分段计数逻辑
- 细噪声竖线：1px 宽，验证宽度过滤
"""

import sys
import pathlib
import random

_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import cv2
import numpy as np

TASK_ID   = "task_longitudinal_groove_vis"
CENTER_DIR = _ROOT / "tests" / "datasets" / TASK_ID / "center_inf"
SIDE_DIR   = _ROOT / "tests" / "datasets" / TASK_ID / "side_inf"

CENTER_DIR.mkdir(parents=True, exist_ok=True)
SIDE_DIR.mkdir(parents=True, exist_ok=True)

H, W = 128, 128
RNG  = np.random.default_rng(42)      # 固定种子，结果可复现
random.seed(42)

# ── 基础工具 ─────────────────────────────────────────────────────────────────

def _background() -> np.ndarray:
    """生成浅灰背景 + 轻微纹理噪声，模拟花纹块表面"""
    base = RNG.integers(170, 200, (H, W), dtype=np.uint8)
    img  = np.stack([base, base, base], axis=-1).astype(np.uint8)
    return img


def _draw_longitudinal_groove(
    img: np.ndarray,
    x_center: int,
    width: int,
    row_start: int = 0,
    row_end: int = H,
    dark_val: int = 30,
) -> np.ndarray:
    """
    在 img 上绘制一条纵向细沟。

    使用交替明暗行（暗行=dark_val，亮行=dark_val+100）模拟真实纹理，
    确保自适应二值化能将暗行检测为前景。

    Parameters
    ----------
    x_center  : 中心列坐标
    width     : 沟槽宽度（px）
    row_start : 起始行
    row_end   : 结束行（不含）
    dark_val  : 暗行灰度值
    """
    out    = img.copy()
    c_l    = max(0, x_center - width // 2)
    c_r    = min(W, c_l + width)
    bright = min(255, dark_val + 100)
    for r in range(row_start, row_end):
        val = dark_val if (r % 2 == 0) else bright
        out[r, c_l:c_r] = val
    return out


def _draw_diagonal_stagger(
    img: np.ndarray,
    x_base: int,
    groove_width: int,
    dark_val: int = 30,
) -> np.ndarray:
    """
    绘制三段水平错位的短暗带，模拟斜沟叠合干扰。

    三段垂直位置：0-30 / 50-80 / 100-127，
    每段水平偏移 3-5px，制造列投影叠合但行方向不连续的效果。
    """
    out      = img.copy()
    bright   = min(255, dark_val + 100)
    segments = [(0, 30, 0), (50, 80, 4), (100, 128, 8)]  # (row_s, row_e, x_offset)
    for r_s, r_e, dx in segments:
        c_l = max(0, x_base + dx - groove_width // 2)
        c_r = min(W, c_l + groove_width)
        for r in range(r_s, r_e):
            val = dark_val if (r % 2 == 0) else bright
            out[r, c_l:c_r] = val
    return out


def _draw_thin_noise(img: np.ndarray, x: int, width: int = 1) -> np.ndarray:
    """绘制细噪声竖线（宽度远小于有效阈值 ~2px）"""
    out = img.copy()
    c_l = max(0, x - width // 2)
    c_r = min(W, c_l + width)
    for r in range(H):
        val = 40 if (r % 2 == 0) else 140
        out[r, c_l:c_r] = val
    return out


def _draw_slanted_groove(
    img: np.ndarray,
    x_center_top: int,
    angle_deg: float,
    width: int = 4,
    row_start: int = 0,
    row_end: int = H,
    dark_val: int = 30,
) -> np.ndarray:
    """
    绘制偏离竖直方向 angle_deg 度的倾斜纵沟。

    使用交替明暗行保证自适应二值化检测。
    angle_deg > 0 向右倾斜，< 0 向左倾斜。
    """
    import math
    out   = img.copy()
    tan_a = math.tan(math.radians(angle_deg))
    bright = min(255, dark_val + 100)
    for r in range(row_start, row_end):
        cx  = int(round(x_center_top + r * tan_a))
        c_l = max(0, cx - width // 2)
        c_r = min(W, c_l + width)
        if c_l < c_r:
            val = dark_val if (r % 2 == 0) else bright
            out[r, c_l:c_r] = val
    return out


# ── 场景生成器 ────────────────────────────────────────────────────────────────

def _save(img: np.ndarray, path: pathlib.Path, label: str):
    cv2.imwrite(str(path), img)
    print(f"  生成: {path.name}  ({label})")


def generate_center_images():
    """生成 center_inf 测试图（RIB2/3/4，允许 0-2 条）"""
    print("\n[center_inf] 生成合成图像...")

    # ── 场景 C1：无纵沟（期望:PASS, count=0）
    img = _background()
    _save(img, CENTER_DIR / "syn_c1_no_groove.png", "无纵沟, 期望PASS/count=0")

    # ── 场景 C2：1 条居中纵沟，宽 4px（期望:PASS, count=1）
    img = _draw_longitudinal_groove(_background(), x_center=64, width=4)
    _save(img, CENTER_DIR / "syn_c2_one_groove_center.png", "1条居中纵沟w=4, 期望PASS/count=1")

    # ── 场景 C3：2 条纵沟，均匀分布（期望:PASS, count=2 边界）
    img = _draw_longitudinal_groove(_background(), x_center=35, width=4)
    img = _draw_longitudinal_groove(img,           x_center=90, width=4)
    _save(img, CENTER_DIR / "syn_c3_two_grooves.png", "2条纵沟, 期望PASS/count=2")

    # ── 场景 C4：3 条纵沟（期望:FAIL, count=3 > 2）
    img = _draw_longitudinal_groove(_background(), x_center=24, width=4)
    img = _draw_longitudinal_groove(img,           x_center=64, width=4)
    img = _draw_longitudinal_groove(img,           x_center=104, width=4)
    _save(img, CENTER_DIR / "syn_c4_three_grooves.png", "3条纵沟, 期望FAIL/count=3")

    # ── 场景 C5：1 条纵沟 + 细噪声竖线（期望:PASS, count=1，噪声被过滤）
    img = _draw_longitudinal_groove(_background(), x_center=64, width=4)
    img = _draw_thin_noise(img, x=40, width=1)
    img = _draw_thin_noise(img, x=90, width=1)
    _save(img, CENTER_DIR / "syn_c5_groove_plus_noise.png", "1条纵沟+2条噪声, 期望PASS/count=1")

    # ── 场景 C6：3段分离短纵沟（期望:FAIL, count=3，按分段分别计数）
    img = _draw_diagonal_stagger(_background(), x_base=64, groove_width=4)
    _save(img, CENTER_DIR / "syn_c6_diagonal_stagger.png", "3段分离短纵沟, 期望FAIL/count=3")

    # ── 场景 C7：随机位置，宽度随机（3-5px）1条（期望:PASS, count=1）
    rng_x = int(RNG.integers(25, 100))
    rng_w = int(RNG.integers(3, 6))
    img   = _draw_longitudinal_groove(_background(), x_center=rng_x, width=rng_w)
    _save(img, CENTER_DIR / f"syn_c7_random_x{rng_x}_w{rng_w}.png",
          f"随机1条 x={rng_x} w={rng_w}, 期望PASS/count=1")

    # ── 场景 C8：纵沟仅覆盖上半图（行0-55），长度 > 图片宽度 1/5（期望:PASS, count=1）
    img = _background()
    img = _draw_longitudinal_groove(img, x_center=64, width=4, row_start=0, row_end=55)
    _save(img, CENTER_DIR / "syn_c8_top_half_only.png", "纵沟仅上半段但长度达标, 期望PASS/count=1")

    # ── 场景 C9：2条纵沟 + 左边缘主沟残留（期望:PASS, count=2，边缘被屏蔽）
    img = _draw_longitudinal_groove(_background(), x_center=40, width=4)
    img = _draw_longitudinal_groove(img,           x_center=90, width=4)
    # 模拟左边缘主沟残留 (cols 0-8)
    for r in range(H):
        val = 25 if (r % 2 == 0) else 80
        img[r, 0:8] = val
    _save(img, CENTER_DIR / "syn_c9_two_grooves_edge_residual.png",
          "2条纵沟+左边缘主沟残留, 期望PASS/count=2")

    # ── 场景 C10：宽度过大（15px，超出 max_w_px≈6）模拟细主沟（期望:PASS, count=0）
    img = _draw_longitudinal_groove(_background(), x_center=64, width=15)
    _save(img, CENTER_DIR / "syn_c10_too_wide.png", "宽度15px过大, 期望PASS/count=0")

    # ── 场景 C11：25° 倾斜纵沟（< 30°，期望:PASS, count=1）
    img = _draw_slanted_groove(_background(), x_center_top=34, angle_deg=25.0, width=4)
    _save(img, CENTER_DIR / "syn_c11_slant_25deg.png", "25°倾斜纵沟, 期望PASS/count=1")

    # ── 场景 C12：35° 倾斜纵沟（> 30°，期望:PASS, count=0，被角度过滤）
    img = _draw_slanted_groove(_background(), x_center_top=20, angle_deg=35.0, width=4)
    _save(img, CENTER_DIR / "syn_c12_slant_35deg.png", "35°倾斜纵沟, 期望PASS/count=0(角度过滤)")


def generate_side_images():
    """生成 side_inf 测试图（RIB1/5，允许 0-1 条）"""
    print("\n[side_inf] 生成合成图像...")

    # ── 场景 S1：无纵沟（期望:PASS, count=0）
    img = _background()
    _save(img, SIDE_DIR / "syn_s1_no_groove.png", "无纵沟, 期望PASS/count=0")

    # ── 场景 S2：1 条纵沟（期望:PASS, count=1）
    img = _draw_longitudinal_groove(_background(), x_center=64, width=4)
    _save(img, SIDE_DIR / "syn_s2_one_groove.png", "1条纵沟, 期望PASS/count=1")

    # ── 场景 S3：2 条纵沟（期望:FAIL, count=2 > 1）
    img = _draw_longitudinal_groove(_background(), x_center=35, width=4)
    img = _draw_longitudinal_groove(img,           x_center=90, width=4)
    _save(img, SIDE_DIR / "syn_s3_two_grooves.png", "2条纵沟超出上限, 期望FAIL/count=2")

    # ── 场景 S4：1 条纵沟 + 细噪声（期望:PASS, count=1）
    img = _draw_longitudinal_groove(_background(), x_center=64, width=4)
    img = _draw_thin_noise(img, x=40, width=1)
    _save(img, SIDE_DIR / "syn_s4_groove_plus_noise.png", "1条纵沟+噪声, 期望PASS/count=1")

    # ── 场景 S5：随机位置，宽度随机 3-5px（期望:PASS, count=1）
    rng_x = int(RNG.integers(30, 95))
    rng_w = int(RNG.integers(3, 6))
    img   = _draw_longitudinal_groove(_background(), x_center=rng_x, width=rng_w)
    _save(img, SIDE_DIR / f"syn_s5_random_x{rng_x}_w{rng_w}.png",
          f"随机1条 x={rng_x} w={rng_w}, 期望PASS/count=1")

    # ── 场景 S6：3段分离短纵沟（期望:FAIL, count=3）
    img = _draw_diagonal_stagger(_background(), x_base=64, groove_width=4)
    _save(img, SIDE_DIR / "syn_s6_diagonal_stagger.png", "3段分离短纵沟, 期望FAIL/count=3")

    # ── 场景 S7：宽度过小（1px）→ 噪声级，期望 count=0（宽度不达标）
    img = _background()
    for r in range(H):
        val = 30 if (r % 2 == 0) else 130
        img[r, 64:65] = val
    _save(img, SIDE_DIR / "syn_s7_too_narrow.png", "宽度1px过细, 期望PASS/count=0")

    # ── 场景 S8：25° 倾斜纵沟（期望:PASS, count=1）
    img = _draw_slanted_groove(_background(), x_center_top=34, angle_deg=25.0, width=4)
    _save(img, SIDE_DIR / "syn_s8_slant_25deg.png", "25°倾斜纵沟, 期望PASS/count=1")


if __name__ == "__main__":
    generate_center_images()
    generate_side_images()
    print("\n完成。图像已保存到:")
    print(f"  center_inf: {CENTER_DIR}")
    print(f"  side_inf:   {SIDE_DIR}")
