# -*- coding: utf-8 -*-
"""
RIB连续性拼接算法模块

Rule 16: RIB2/3/4横沟/钢片任意组合连续性
Rule 17: RIB1/2和RIB4/5可连续可不连续（50%概率）

实现方法：
- 中间双RIB连续（RIB2-RIB3 或 RIB3-RIB4）：拉宽1条center到2x，切分出2条连续RIB
- 中间三RIB连续（RIB2-RIB3-RIB4）：拉宽2条center各1.5x，拼接后三等分
- 边缘连续（RIB1-RIB2 或 RIB4-RIB5）：拉宽side到1.25x，与center融合
"""

import cv2
import json
import numpy as np
import os
import random
from typing import List, Tuple, Dict, Optional

from utils.logger import get_logger

logger = get_logger("rib_continuity_stitch")


# ==================== 基础工具函数 ====================

def trim_residual_grooves(image: np.ndarray, threshold: int = 30, max_trim_px: int = 20) -> np.ndarray:
    """
    裁掉RIB图像边缘残留的主沟（黑色列）

    Args:
        image: BGR图像
        threshold: 黑色判定阈值（列平均亮度低于此值视为黑色）
        max_trim_px: 单侧最大裁剪像素数
    Returns:
        裁剪后的图像
    """
    h, w = image.shape[:2]
    if w <= max_trim_px * 2:
        return image

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    col_mean = gray.mean(axis=0)

    # 从左侧找第一个非黑列
    left = 0
    for i in range(min(max_trim_px, w)):
        if col_mean[i] > threshold:
            left = i
            break

    # 从右侧找最后一个非黑列
    right = w
    for i in range(w - 1, max(w - max_trim_px - 1, -1), -1):
        if col_mean[i] > threshold:
            right = i + 1
            break

    if left >= right or (right - left) < w * 0.5:
        return image

    trimmed = image[:, left:right].copy()
    if left > 0 or right < w:
        logger.debug(f"裁剪残留主沟: 左裁{left}px, 右裁{w - right}px, {w} -> {trimmed.shape[1]}")
    return trimmed


def widen_image(image: np.ndarray, scale: float) -> np.ndarray:
    """水平拉宽图像"""
    h, w = image.shape[:2]
    new_w = int(round(w * scale))
    return cv2.resize(image, (new_w, h), interpolation=cv2.INTER_LINEAR)


def normalize_height(images: List[np.ndarray]) -> List[np.ndarray]:
    """统一图像高度（取最小高度，从顶部裁剪）"""
    if not images:
        return images
    target_h = min(img.shape[0] for img in images)
    return [img[:target_h].copy() if img.shape[0] > target_h else img for img in images]


def create_groove_strip(height: int, width: int) -> np.ndarray:
    """创建黑色主沟条带"""
    return np.zeros((height, width, 3), dtype=np.uint8)


# ==================== 连续性构建函数 ====================

def build_center_ribs(
    center_images: List[np.ndarray],
    center_mode: str,
    blend_width: int = 10
) -> Tuple[List[np.ndarray], List[str]]:
    """
    根据连续性模式构建中间3个RIB (RIB2, RIB3, RIB4)

    Args:
        center_images: center RIB图像列表（至少1张）
        center_mode: 连续性模式
        blend_width: 融合区域宽度

    Returns:
        (rib_list, description_list)
    """
    if not center_images:
        raise ValueError("至少需要1张center图像")

    c0 = center_images[0]
    c1 = center_images[1 % len(center_images)]
    c2 = center_images[2 % len(center_images)]
    target_w = c0.shape[1]

    if center_mode == "RIB2-RIB3":
        # 拉宽c0到2x，切分出RIB2+RIB3（连续），c1作RIB4
        widened = widen_image(c0, 2.0)
        mid = widened.shape[1] // 2
        rib2 = widened[:, :mid]
        rib3 = widened[:, mid:mid + target_w]
        rib4 = c1
        descriptions = [
            f"RIB2: center[0] widen 2x left-half (w={rib2.shape[1]})",
            f"RIB3: center[0] widen 2x right-half (w={rib3.shape[1]})",
            f"RIB4: center[1] original (w={rib4.shape[1]})",
            ">> RIB2-RIB3 CONTINUOUS",
        ]
        return [rib2, rib3, rib4], descriptions

    elif center_mode == "RIB3-RIB4":
        # c0作RIB2，拉宽c1到2x切分出RIB3+RIB4（连续）
        rib2 = c0
        widened = widen_image(c1, 2.0)
        mid = widened.shape[1] // 2
        rib3 = widened[:, :mid]
        rib4 = widened[:, mid:mid + target_w]
        descriptions = [
            f"RIB2: center[0] original (w={rib2.shape[1]})",
            f"RIB3: center[1] widen 2x left-half (w={rib3.shape[1]})",
            f"RIB4: center[1] widen 2x right-half (w={rib4.shape[1]})",
            ">> RIB3-RIB4 CONTINUOUS",
        ]
        return [rib2, rib3, rib4], descriptions

    elif center_mode == "RIB2-RIB3-RIB4":
        # 拉宽c0和c1各1.5x，拼接后三等分 -> 全连续
        w0 = widen_image(c0, 1.5)
        w1 = widen_image(c1, 1.5)

        # 统一高度
        h = min(w0.shape[0], w1.shape[0])
        w0, w1 = w0[:h], w1[:h]

        # 拼接（在接缝处融合）
        bw = min(blend_width, w0.shape[1] // 4, w1.shape[1] // 4)
        if bw > 0:
            left_part = w0[:, :w0.shape[1] - bw]
            right_part = w1[:, bw:]
            overlap_l = w0[:, w0.shape[1] - bw:].astype(np.float32)
            overlap_r = w1[:, :bw].astype(np.float32)
            alpha = np.linspace(1, 0, bw).reshape(1, bw, 1)
            blended = (overlap_l * alpha + overlap_r * (1 - alpha)).astype(np.uint8)
            combined = np.hstack([left_part, blended, right_part])
        else:
            combined = np.hstack([w0, w1])

        # 三等分
        total_w = combined.shape[1]
        rib_w = total_w // 3
        rib2 = combined[:, :rib_w]
        rib3 = combined[:, rib_w:2 * rib_w]
        rib4 = combined[:, 2 * rib_w:3 * rib_w]

        descriptions = [
            f"RIB2: center[0]+[1] each 1.5x, combined 1/3 (w={rib2.shape[1]})",
            f"RIB3: center[0]+[1] each 1.5x, combined 2/3 (w={rib3.shape[1]})",
            f"RIB4: center[0]+[1] each 1.5x, combined 3/3 (w={rib4.shape[1]})",
            ">> RIB2-RIB3-RIB4 ALL CONTINUOUS",
        ]
        return [rib2, rib3, rib4], descriptions

    else:
        # "none" 或默认：不连续，直接使用原始center图像
        descriptions = [
            f"RIB2: center[0] original (w={c0.shape[1]})",
            f"RIB3: center[1] original (w={c1.shape[1]})",
            f"RIB4: center[2] original (w={c2.shape[1]})",
            ">> NO center continuity",
        ]
        return [c0.copy(), c1.copy(), c2.copy()], descriptions


def build_edge_ribs(
    side_left: np.ndarray,
    side_right: np.ndarray,
    center_rib2: np.ndarray,
    center_rib4: np.ndarray,
    rib12_continuous: bool,
    rib45_continuous: bool,
    blend_width: int = 10
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """
    处理边缘RIB对的连续性（Rule 17）

    Args:
        side_left: 左侧RIB1图像
        side_right: 右侧RIB5图像
        center_rib2: 中间RIB2图像
        center_rib4: 中间RIB4图像
        rib12_continuous: RIB1-RIB2是否连续
        rib45_continuous: RIB4-RIB5是否连续
        blend_width: 融合宽度

    Returns:
        (rib1, rib2, rib4, rib5, descriptions)
    """
    descriptions = []
    rib1 = side_left.copy()
    rib2 = center_rib2.copy()
    rib4 = center_rib4.copy()
    rib5 = side_right.copy()

    if rib12_continuous:
        # RIB1-RIB2连续：拉宽side到1.25x
        widened = widen_image(side_left, 1.25)
        extra_w = widened.shape[1] - side_left.shape[1]
        overlap = min(extra_w, center_rib2.shape[1] // 2)

        if overlap > 0:
            h = min(widened.shape[0], center_rib2.shape[0])
            widened_h = widened[:h]
            rib2_h = center_rib2[:h]

            # RIB1保持原始宽度
            rib1 = widened_h[:, :side_left.shape[1]]

            # RIB2：在左侧融合widened的额外部分
            extra_part = widened_h[:, side_left.shape[1]:side_left.shape[1] + overlap].astype(np.float32)
            center_left = rib2_h[:, :overlap].astype(np.float32)
            alpha = np.linspace(1, 0, overlap).reshape(1, overlap, 1)
            blended = (extra_part * alpha + center_left * (1 - alpha)).astype(np.uint8)
            rib2 = np.hstack([blended, rib2_h[:, overlap:]])

            descriptions.append(f"RIB1-RIB2 CONTINUOUS: side widen 1.25x, overlap={overlap}px")
        else:
            descriptions.append("RIB1-RIB2 CONTINUOUS: overlap too small, skipped blend")
    else:
        descriptions.append("RIB1-RIB2 NOT continuous")

    if rib45_continuous:
        # RIB4-RIB5连续：拉宽side到1.25x
        widened = widen_image(side_right, 1.25)
        extra_w = widened.shape[1] - side_right.shape[1]
        overlap = min(extra_w, center_rib4.shape[1] // 2)

        if overlap > 0:
            h = min(center_rib4.shape[0], widened.shape[0])
            rib4_h = center_rib4[:h]
            widened_h = widened[:h]

            # RIB5保持原始宽度（取widened右侧）
            rib5 = widened_h[:, widened_h.shape[1] - side_right.shape[1]:]

            # RIB4：在右侧融合widened的额外部分
            center_right = rib4_h[:, rib4_h.shape[1] - overlap:].astype(np.float32)
            extra_part = widened_h[:, :overlap].astype(np.float32)
            alpha = np.linspace(1, 0, overlap).reshape(1, overlap, 1)
            blended = (center_right * alpha + extra_part * (1 - alpha)).astype(np.uint8)
            rib4 = np.hstack([rib4_h[:, :rib4_h.shape[1] - overlap], blended])

            descriptions.append(f"RIB4-RIB5 CONTINUOUS: side widen 1.25x, overlap={overlap}px")
        else:
            descriptions.append("RIB4-RIB5 CONTINUOUS: overlap too small, skipped blend")
    else:
        descriptions.append("RIB4-RIB5 NOT continuous")

    return rib1, rib2, rib4, rib5, descriptions


# ==================== 调试图绘制 ====================

def draw_debug_image(
    full_image: np.ndarray,
    rib_boundaries: List[Tuple[int, int]],
    groove_width_px: int,
    descriptions: List[str],
    continuity_info: dict
) -> np.ndarray:
    """
    在完整胎面图的主沟区域标注"连续"或"不连续"

    Args:
        full_image: 完整胎面BGR图像
        rib_boundaries: 各RIB的(x_start, x_end)列表
        groove_width_px: 主沟宽度
        descriptions: （未使用，详细信息在JSON中）
        continuity_info: 连续性信息

    Returns:
        带连续性标注的调试图像
    """
    h, w = full_image.shape[:2]

    # 顶部留白
    top_bar = 30
    canvas = np.ones((top_bar + h, w, 3), dtype=np.uint8) * 255
    canvas[top_bar:top_bar + h, :w] = full_image

    font = cv2.FONT_HERSHEY_SIMPLEX
    center_mode = continuity_info.get("center_mode", "")
    rib12 = continuity_info.get("edge_rib12", False)
    rib45 = continuity_info.get("edge_rib45", False)

    # 判定每个主沟间隙的连续性
    groove_continuity = {
        0: rib12,                                                          # RIB1-RIB2
        1: center_mode in ("RIB2-RIB3", "RIB2-RIB3-RIB4"),               # RIB2-RIB3
        2: center_mode in ("RIB3-RIB4", "RIB2-RIB3-RIB4"),               # RIB3-RIB4
        3: rib45,                                                          # RIB4-RIB5
    }

    for idx in range(len(rib_boundaries) - 1):
        x1 = rib_boundaries[idx][1]       # 左RIB右边界
        x2 = rib_boundaries[idx + 1][0]   # 右RIB左边界
        mid_x = (x1 + x2) // 2

        is_cont = groove_continuity.get(idx, False)
        label = "Y" if is_cont else "N"
        color = (0, 0, 255) if is_cont else (180, 180, 180)  # 红=连续, 灰=不连续

        # 在顶部留白区标注
        text_size = cv2.getTextSize(label, font, 0.6, 2)[0]
        tx = mid_x - text_size[0] // 2
        cv2.putText(canvas, label, (tx, 22), font, 0.6, color, 2, cv2.LINE_AA)

        # 在主沟区域中间画竖线标记
        line_color = (0, 0, 255) if is_cont else (200, 200, 200)
        cv2.line(canvas, (mid_x, top_bar), (mid_x, top_bar + h), line_color, 1, cv2.LINE_AA)

    return canvas


# ==================== 主拼接函数 ====================

def stitch_with_continuity(
    center_images: List[np.ndarray],
    side_images: List[np.ndarray],
    continuity_config: Optional[dict] = None,
    groove_width_px: int = 20,
    blend_width: int = 10,
    debug_dir: Optional[str] = None,
    source_names: Optional[dict] = None
) -> Tuple[np.ndarray, dict]:
    """
    Rule 16/17: 根据连续性配置拼接RIB图像生成完整胎面图

    Args:
        center_images: center RIB图像列表 (BGR)，至少1张
        side_images: side RIB图像列表 (BGR)，[left_side, right_side] 或仅1张
        continuity_config: 连续性配置
            - center_mode: "RIB2-RIB3" | "RIB3-RIB4" | "RIB2-RIB3-RIB4" | "none"
            - edge_rib12: True/False/None (None=50%随机)
            - edge_rib45: True/False/None (None=50%随机)
        groove_width_px: 主沟宽度 (像素)，默认20（约10mm, pixel_per_mm≈2）
        blend_width: 拼接融合区域宽度
        debug_dir: 调试图输出目录
        source_names: 源文件名映射信息

    Returns:
        (full_tread_image, info_dict)
    """
    if continuity_config is None:
        continuity_config = {
            "center_mode": "RIB2-RIB3-RIB4",
            "edge_rib12": None,
            "edge_rib45": None
        }

    center_mode = continuity_config.get("center_mode", "RIB2-RIB3-RIB4")
    edge_rib12 = continuity_config.get("edge_rib12")
    edge_rib45 = continuity_config.get("edge_rib45")

    # Rule 17: None -> 50% 随机
    if edge_rib12 is None:
        edge_rib12 = random.random() < 0.5
    if edge_rib45 is None:
        edge_rib45 = random.random() < 0.5

    if not center_images:
        raise ValueError("center图像列表不能为空")
    if not side_images:
        raise ValueError("side图像列表不能为空")

    # Step 1: 裁剪残留主沟
    center_trimmed = [trim_residual_grooves(img) for img in center_images]
    side_trimmed = [trim_residual_grooves(img) for img in side_images]

    # Step 2: 统一高度
    all_imgs = center_trimmed + side_trimmed
    all_imgs = normalize_height(all_imgs)
    n_center = len(center_trimmed)
    center_trimmed = all_imgs[:n_center]
    side_trimmed = all_imgs[n_center:]

    side_left = side_trimmed[0]
    side_right = side_trimmed[-1] if len(side_trimmed) > 1 else side_trimmed[0]

    # Step 3: 构建中间3个RIB
    center_ribs, center_descs = build_center_ribs(center_trimmed, center_mode, blend_width)

    # Step 4: 处理边缘连续性
    rib1, rib2, rib4, rib5, edge_descs = build_edge_ribs(
        side_left, side_right,
        center_ribs[0], center_ribs[2],
        edge_rib12, edge_rib45,
        blend_width
    )
    # 更新center_ribs中被边缘处理修改的RIB
    center_ribs[0] = rib2
    center_ribs[2] = rib4

    # Step 5: 组装全部5个RIB
    all_ribs = [rib1] + center_ribs + [rib5]
    all_ribs = normalize_height(all_ribs)
    target_h = all_ribs[0].shape[0]

    # Step 6: 拼接 RIB1 | groove | RIB2 | groove | RIB3 | groove | RIB4 | groove | RIB5
    groove = create_groove_strip(target_h, groove_width_px)
    parts = []
    rib_boundaries = []
    current_x = 0

    for i, rib in enumerate(all_ribs):
        x_start = current_x
        x_end = current_x + rib.shape[1]
        rib_boundaries.append((x_start, x_end))
        parts.append(rib)
        current_x = x_end
        if i < len(all_ribs) - 1:
            parts.append(groove)
            current_x += groove_width_px

    full_image = np.hstack(parts)

    # 汇总信息
    all_descs = center_descs + edge_descs
    info = {
        "center_mode": center_mode,
        "edge_rib12_continuous": edge_rib12,
        "edge_rib45_continuous": edge_rib45,
        "groove_width_px": groove_width_px,
        "rib_widths": [rib.shape[1] for rib in all_ribs],
        "rib_boundaries": rib_boundaries,
        "full_image_size": (full_image.shape[1], full_image.shape[0]),
        "descriptions": all_descs,
        "source_names": source_names or {},
        "main_groove_positions": [],
        "continuity_map": {
            "RIB2-RIB3": center_mode in ("RIB2-RIB3", "RIB2-RIB3-RIB4"),
            "RIB3-RIB4": center_mode in ("RIB3-RIB4", "RIB2-RIB3-RIB4"),
            "RIB1-RIB2": edge_rib12,
            "RIB4-RIB5": edge_rib45,
        },
    }

    # 计算主沟中心X坐标
    for i in range(len(rib_boundaries) - 1):
        groove_center = (rib_boundaries[i][1] + rib_boundaries[i + 1][0]) // 2
        info["main_groove_positions"].append(groove_center)

    # Step 7: 调试输出
    if debug_dir:
        os.makedirs(debug_dir, exist_ok=True)

        # 保存原始输入图像
        input_dir = os.path.join(debug_dir, "input")
        os.makedirs(input_dir, exist_ok=True)
        for i, img in enumerate(center_images):
            cv2.imwrite(os.path.join(input_dir, f"center_{i}.png"), img)
        for i, img in enumerate(side_images):
            cv2.imwrite(os.path.join(input_dir, f"side_{i}.png"), img)

        # 保存各RIB
        rib_labels = ["RIB1_side", "RIB2_center", "RIB3_center", "RIB4_center", "RIB5_side"]
        for i, (rib, label) in enumerate(zip(all_ribs, rib_labels)):
            cv2.imwrite(os.path.join(debug_dir, f"{label}.png"), rib)

        # 保存原始结果
        cv2.imwrite(os.path.join(debug_dir, "full_tread.png"), full_image)

        # 保存仅标注连续/不连续的调试图
        debug_img = draw_debug_image(
            full_image, rib_boundaries, groove_width_px,
            all_descs,
            {
                "center_mode": center_mode,
                "edge_rib12": edge_rib12,
                "edge_rib45": edge_rib45,
            }
        )
        cv2.imwrite(os.path.join(debug_dir, "debug_annotated.png"), debug_img)

        # 保存详细说明到JSON
        debug_json = {
            "center_mode": center_mode,
            "continuity_map": info["continuity_map"],
            "edge_rib12_continuous": edge_rib12,
            "edge_rib45_continuous": edge_rib45,
            "groove_width_px": groove_width_px,
            "full_image_size": {"width": full_image.shape[1], "height": full_image.shape[0]},
            "input_images": {
                "center": [
                    {"index": i, "width": img.shape[1], "height": img.shape[0], "file": f"input/center_{i}.png"}
                    for i, img in enumerate(center_images)
                ],
                "side": [
                    {"index": i, "width": img.shape[1], "height": img.shape[0], "file": f"input/side_{i}.png"}
                    for i, img in enumerate(side_images)
                ],
            },
            "ribs": [],
            "main_grooves": [],
            "descriptions": all_descs,
            "source_names": source_names or {},
        }
        for i, (rib, label) in enumerate(zip(all_ribs, rib_labels)):
            debug_json["ribs"].append({
                "index": i + 1,
                "label": label,
                "type": "side" if i in (0, 4) else "center",
                "width": rib.shape[1],
                "height": rib.shape[0],
                "x_start": rib_boundaries[i][0],
                "x_end": rib_boundaries[i][1],
                "file": f"{label}.png",
            })
        groove_pairs = ["RIB1-RIB2", "RIB2-RIB3", "RIB3-RIB4", "RIB4-RIB5"]
        for i, pos in enumerate(info["main_groove_positions"]):
            debug_json["main_grooves"].append({
                "pair": groove_pairs[i],
                "center_x": pos,
                "width_px": groove_width_px,
                "continuous": info["continuity_map"].get(groove_pairs[i], False),
            })

        json_path = os.path.join(debug_dir, "debug_info.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(debug_json, f, ensure_ascii=False, indent=2)

        info["debug_dir"] = debug_dir
        logger.info(f"调试图已保存到: {debug_dir}")

    return full_image, info
