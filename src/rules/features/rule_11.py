# -*- coding: utf-8 -*-
"""
Rule 11 特征提取：纵向细沟 & 纵向钢片数量检测。
调用 src.core.detection.longitudinal_groove。
"""
from __future__ import annotations
import numpy as np
from typing import Any, Dict
from src.core.detection.longitudinal_groove import detect_longitudinal_grooves


def extract(
    image: np.ndarray,
    image_type: str,
    groove_width_mm: float = 0.34,
    pixel_per_mm: float = 11.81,
    min_width_offset_px: int = 1,
    edge_margin_ratio: float = 0.10,
    min_segment_length_ratio: float = 0.12,
    max_angle_deg: float = 30.0,
) -> Dict[str, Any]:
    """
    Returns
    -------
    dict
        num_longitudinal_grooves : int
        groove_segments / …（来自 core 层）
    """
    details = detect_longitudinal_grooves(
        image, image_type,
        groove_width_mm=groove_width_mm,
        pixel_per_mm=pixel_per_mm,
        min_width_offset_px=min_width_offset_px,
        edge_margin_ratio=edge_margin_ratio,
        min_segment_length_ratio=min_segment_length_ratio,
        max_angle_deg=max_angle_deg,
    )
    return details
