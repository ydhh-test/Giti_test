# symmetry_check.py
import cv2
import numpy as np
from typing import Dict, Tuple
from skimage.metrics import structural_similarity as ssim


def _to_gray(img_bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)


def _resize_to_same(a: np.ndarray, b: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    将两张灰度图裁剪到相同尺寸（取最小宽高）
    """
    ha, wa = a.shape[:2]
    hb, wb = b.shape[:2]
    h = min(ha, hb)
    w = min(wa, wb)
    return a[:h, :w], b[:h, :w]


def symmetry_score_mirror(tdw_bgr: np.ndarray,
                          center_x: int,
                          allow_shift_px: int = 0) -> Dict:
    """
    镜像对称检测（细则3为主）
    - center_x: 中心线x坐标（由外部检测）
    - allow_shift_px:
        0  表示严格镜像
        >0 表示允许左右错位（细则4）

    输出：
    {
        "best_score": float (0~1),
        "best_shift": int,
        "method": "ssim_mirror"
    }
    """
    gray = _to_gray(tdw_bgr)

    H, W = gray.shape[:2]
    center_x = max(5, min(W - 5, int(center_x)))

    left = gray[:, :center_x]
    right = gray[:, center_x:]

    # 右侧翻转
    right_flip = cv2.flip(right, 1)

    # 对齐尺寸
    left, right_flip = _resize_to_same(left, right_flip)

    # SSIM需要uint8
    left_u8 = left.astype(np.uint8)
    right_u8 = right_flip.astype(np.uint8)

    # shift搜索
    best_score = -1.0
    best_shift = 0

    # shift定义：对 right_flip 做水平平移
    for shift in range(-allow_shift_px, allow_shift_px + 1):
        if shift == 0:
            a = left_u8
            b = right_u8
        else:
            # 平移裁剪对齐（不填充，直接裁掉边缘）
            if shift > 0:
                a = left_u8[:, shift:]
                b = right_u8[:, :-shift]
            else:
                s = -shift
                a = left_u8[:, :-s]
                b = right_u8[:, s:]

        if a.size == 0 or b.size == 0:
            continue

        # SSIM
        score = float(ssim(a, b, data_range=255))

        if score > best_score:
            best_score = score
            best_shift = shift

    return {
        "best_score": float(best_score),
        "best_shift": int(best_shift),
        "method": "ssim_mirror",
        "allow_shift_px": int(allow_shift_px)
    }


def symmetry_pass(score: float, threshold: float = 0.90) -> Dict:
    """
    对称性通过判定
    """
    return {
        "passed": bool(score >= threshold),
        "threshold": float(threshold)
    }
