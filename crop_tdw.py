
# crop_tdw.py
import cv2
import numpy as np
from typing import Dict, Tuple


def _to_gray(img_bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)


def _binary_land_mask(gray: np.ndarray,
                      blur_ksize: int = 5,
                      use_otsu: bool = True,
                      fixed_thr: int = 240) -> np.ndarray:
    """
    将“非白色区域”提取出来：
    - 白底为背景
    - 黑/灰线条为花纹
    输出: 0/255 二值mask
    """
    g = gray.copy()

    if blur_ksize and blur_ksize >= 3:
        g = cv2.GaussianBlur(g, (blur_ksize, blur_ksize), 0)

    if use_otsu:
        # Otsu 会自动找到阈值
        _, bin_inv = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        # 固定阈值：灰度 < fixed_thr 认为是花纹
        _, bin_inv = cv2.threshold(g, fixed_thr, 255, cv2.THRESH_BINARY_INV)

    return bin_inv


def crop_tdw_region(img_bgr: np.ndarray,
                    padding: int = 10,
                    min_area_ratio: float = 0.00000001) -> Tuple[np.ndarray, Dict]:
    """
    自动裁剪 TDW 区域：
    1) 提取花纹mask（非白区域）
    2) 找最大轮廓
    3) 用外接矩形裁剪
    4) 返回裁剪后的TDW图，以及裁剪信息

    min_area_ratio:
        最大轮廓面积必须占整图面积的比例，否则认为失败
    """
    H, W = img_bgr.shape[:2]
    gray = _to_gray(img_bgr)
    mask = _binary_land_mask(gray)

    # 形态学闭运算：填补断裂
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise RuntimeError("TDW裁剪失败：未检测到任何轮廓")

    # 找最大轮廓
    areas = [cv2.contourArea(c) for c in contours]
    idx = int(np.argmax(areas))
    max_contour = contours[idx]
    max_area = areas[idx]

    if max_area < (H * W * min_area_ratio):
        raise RuntimeError(
            f"TDW裁剪失败：最大轮廓面积过小 max_area={max_area}, image_area={H*W}"
        )

    x, y, w, h = cv2.boundingRect(max_contour)

    # 加 padding
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(W, x + w + padding)
    y2 = min(H, y + h + padding)

    tdw = img_bgr[y1:y2, x1:x2].copy()

    info = {
        "crop_box_xyxy": (int(x1), int(y1), int(x2), int(y2)),
        "crop_box_xywh": (int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
        "max_contour_area": float(max_area),
        "image_size": (int(W), int(H)),
        "tdw_size": (int(x2 - x1), int(y2 - y1))
    }
    return tdw, info


def detect_centerline_x(tdw_bgr: np.ndarray,
                        use_otsu: bool = True) -> int:
    """
    自动检测中心线位置 center_x
    技术：垂直投影（统计每一列的非白像素数量）
    """
    gray = _to_gray(tdw_bgr)
    mask = _binary_land_mask(gray, use_otsu=use_otsu)

    # mask: 0/255，转为 0/1
    m = (mask > 0).astype(np.uint8)

    # 每列非白像素数量
    col_sum = np.sum(m, axis=0)

    # center_x 取最大峰值
    center_x = int(np.argmax(col_sum))

    # 防止极端情况：落在边缘
    W = tdw_bgr.shape[1]
    center_x = max(5, min(W - 5, center_x))
    return center_x
