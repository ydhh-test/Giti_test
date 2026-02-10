# land_sea_ratio.py
import cv2
import numpy as np
from typing import Dict


def compute_land_sea_ratio(tdw_bgr: np.ndarray,
                           use_otsu: bool = True,
                           fixed_thr: int = 240,
                           blur_ksize: int = 3,
                           morph_open: bool = True) -> Dict:
    """
    海陆比计算（细则13）：
    land_sea_ratio = (黑色面积 + 灰色面积) / 总面积

    返回：
    {
        "land_sea_ratio": float,
        "land_pixels": int,
        "total_pixels": int,
        "mask_land": np.ndarray (0/255)
    }
    """
    gray = cv2.cvtColor(tdw_bgr, cv2.COLOR_BGR2GRAY)

    if blur_ksize and blur_ksize >= 3:
        gray = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)

    if use_otsu:
        _, mask_land = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        _, mask_land = cv2.threshold(gray, fixed_thr, 255, cv2.THRESH_BINARY_INV)

    if morph_open:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask_land = cv2.morphologyEx(mask_land, cv2.MORPH_OPEN, kernel, iterations=1)

    land_pixels = int(np.sum(mask_land > 0))
    total_pixels = int(mask_land.shape[0] * mask_land.shape[1])

    ratio = float(land_pixels / max(1, total_pixels))

    return {
        "land_sea_ratio": ratio,
        "land_pixels": land_pixels,
        "total_pixels": total_pixels,
        "mask_land": mask_land
    }


def filter_by_land_sea_ratio(land_sea_ratio: float,
                             low: float = 0.20,
                             high: float = 0.50) -> Dict:
    """
    过滤规则：海陆比必须在 [low, high]
    """
    passed = (low <= land_sea_ratio <= high)
    return {
        "passed": bool(passed),
        "threshold_low": float(low),
        "threshold_high": float(high)
    }
