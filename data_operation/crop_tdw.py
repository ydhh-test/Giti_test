# data_operation/crop_tdw.py
import cv2
import numpy as np


def _to_gray(img_bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)


def _binary_land_mask(gray: np.ndarray,
                      blur_ksize: int = 5,
                      use_otsu: bool = True,
                      fixed_thr: int = 240) -> np.ndarray:
    """
    将“非白色区域”提取出来：
    输出: 0/255 二值mask
    """
    g = gray.copy()

    if blur_ksize and blur_ksize >= 3:
        g = cv2.GaussianBlur(g, (blur_ksize, blur_ksize), 0)

    if use_otsu:
        _, bin_inv = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        _, bin_inv = cv2.threshold(g, fixed_thr, 255, cv2.THRESH_BINARY_INV)

    return bin_inv


def detect_centerline_x(tdw_bgr: np.ndarray,
                        use_otsu: bool = True) -> int:
    """
    检测中心线 center_x：
    - 只根据主沟从左到右的顺序编号
    - 4条主沟：center = (第2条 + 第3条)/2
    - 3条主沟：center = 第2条
    """
    gray = _to_gray(tdw_bgr)
    mask = _binary_land_mask(gray, use_otsu=use_otsu)

    m = (mask > 0).astype(np.uint8)
    col_sum = np.sum(m, axis=0).astype(np.float32)

    H, W = m.shape

    # 只在中间区域找（防止边缘噪声）
    left = int(W * 0.15)
    right = int(W * 0.85)
    proj = col_sum[left:right].copy()

    # 平滑（非常重要）
    proj = cv2.GaussianBlur(proj.reshape(1, -1), (1, 51), 0).reshape(-1)

    # 阈值：过滤弱峰（可调）
    thr = proj.max() * 0.55
    idxs = np.where(proj >= thr)[0]

    if len(idxs) == 0:
        center_x = int(left + np.argmax(proj))
        return max(5, min(W - 5, center_x))

    # 把连续区域合并成一个峰（取中心点）
    peaks = []
    start = idxs[0]
    prev = idxs[0]
    for i in idxs[1:]:
        if i == prev + 1:
            prev = i
        else:
            peaks.append((start + prev) // 2)
            start = i
            prev = i
    peaks.append((start + prev) // 2)

    # 映射回原图坐标
    peaks = [p + left for p in peaks]

    # ⭐ 关键：只按从左到右排序（完全符合你的要求）
    peaks = sorted(peaks)

    # ---------------------------
    # ⭐ 从所有峰中选出“主沟”
    # 思路：主沟应该是比较均匀分布的
    # 我们优先取最靠近中心的 3~4 个峰
    # ---------------------------

    # 如果峰太多，只保留距离图像中心最近的前 6 个
    cx = W / 2
    if len(peaks) > 6:
        peaks = sorted(peaks, key=lambda x: abs(x - cx))[:6]
        peaks = sorted(peaks)  # 再按左右排序

    # 现在 peaks 是按左右排序的候选沟
    n = len(peaks)

    if n >= 4:
        # 取最中间的4条作为主沟（更符合轮胎结构）
        mid = n // 2
        # 例如 n=6 -> 取 peaks[1:5]
        selected = peaks[max(0, mid - 2): max(0, mid - 2) + 4]

        # 防止切片不够
        if len(selected) < 4:
            selected = peaks[:4]

        x2, x3 = selected[1], selected[2]
        center_x = int((x2 + x3) / 2)

    elif n == 3:
        # 三条主沟：中心线在第二条主沟上
        center_x = int(peaks[1])

    elif n == 2:
        # 兜底：两条就取中点
        center_x = int((peaks[0] + peaks[1]) / 2)

    else:
        # 只有1条峰：兜底用它
        center_x = int(peaks[0])

    center_x = max(5, min(W - 5, center_x))
    return center_x


# def detect_centerline_x(tdw_bgr: np.ndarray,
#                         use_otsu: bool = True) -> int:
#     """
#     检测中心线 center_x：
#     - 先用垂直投影找出主沟（多个峰）
#     - 若 4 条主沟：center = (x2 + x3) / 2
#     - 若 3 条主沟：center = x2
#     """
#     gray = _to_gray(tdw_bgr)
#     mask = _binary_land_mask(gray, use_otsu=use_otsu)

#     # mask: 0/255，转为 0/1
#     m = (mask > 0).astype(np.uint8)

#     # 每列非白像素数量（主沟越黑，这个值越大）
#     col_sum = np.sum(m, axis=0).astype(np.float32)

#     H, W = m.shape

#     # ⭐ 只在中间 60% 范围找主沟（避免边缘噪声）
#     left = int(W * 0.2)
#     right = int(W * 0.8)
#     proj = col_sum[left:right].copy()

#     # ⭐ 平滑投影（非常重要，否则会出现大量假峰）
#     proj = cv2.GaussianBlur(proj.reshape(1, -1), (1, 31), 0).reshape(-1)

#     # ⭐ 找峰：用阈值过滤掉弱峰
#     # 阈值 = 最大值的 60%（可调）
#     thr = proj.max() * 0.5
#     peak_candidates = np.where(proj >= thr)[0]

#     if len(peak_candidates) == 0:
#         # 兜底：退回最大峰
#         center_x = int(left + np.argmax(proj))
#         return max(5, min(W - 5, center_x))

#     # ⭐ 将连续的 peak 区域合并成一个峰（取每段的中心）
#     peaks = []
#     start = peak_candidates[0]
#     prev = peak_candidates[0]

#     for idx in peak_candidates[1:]:
#         if idx == prev + 1:
#             prev = idx
#         else:
#             # 一段结束
#             peaks.append((start + prev) // 2)
#             start = idx
#             prev = idx
#     peaks.append((start + prev) // 2)

#     # 映射回原图坐标
#     peaks = [p + left for p in peaks]

#     # ⭐ 如果峰太多，只保留最可能的主沟（按投影强度排序）
#     # 取前 6 个峰再排序，防止噪声影响
#     peaks = sorted(peaks, key=lambda x: col_sum[x], reverse=True)[:6]
#     peaks = sorted(peaks)

#     # ⭐ 主沟数量判断（优先 4，再 3）
#     if len(peaks) >= 4:
#         x2 = peaks[1]
#         x3 = peaks[2]
#         center_x = int((x2 + x3) / 2)
#     elif len(peaks) == 3:
#         center_x = int(peaks[1])
#     else:
#         # 峰不够时，兜底：取所有峰的均值
#         center_x = int(np.mean(peaks))

#     center_x = max(5, min(W - 5, center_x))
#     return center_x

