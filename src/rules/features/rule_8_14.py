# -*- coding: utf-8 -*-
"""
Rule 8 / Rule 14 特征提取：横沟数量 & 交点数量检测。
调用 src.core.detection.groove_intersection，返回原始特征。
"""
from __future__ import annotations
import numpy as np
from typing import Any, Dict, Optional
from src.core.detection.groove_intersection import detect_transverse_grooves


def extract(
    image: np.ndarray,
    image_type: str,
    groove_width_mm: Optional[Dict[str, float]] = None,
    pixel_per_mm: float = 7.1,
) -> Dict[str, Any]:
    """
    Parameters
    ----------
    image : np.ndarray
        BGR 小图 (128, 128, 3)。
    image_type : str
        "center" 或 "side"。

    Returns
    -------
    dict
        rib_type, groove_count, groove_positions,
        intersection_count, groove_mask, debug_image
    """
    return detect_transverse_grooves(image, image_type, groove_width_mm, pixel_per_mm)
