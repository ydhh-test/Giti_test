# -*- coding: utf-8 -*-
"""
Rule 6_1 特征提取：节距纵向图案连续性检测。
调用 src.core.detection.pattern_continuity，返回 is_continuous 特征。
"""
from __future__ import annotations
import numpy as np
from typing import Any, Dict
from src.core.detection.pattern_continuity import detect_pattern_continuity


def extract(image: np.ndarray, conf: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parameters
    ----------
    image : np.ndarray
        灰度小图 (H, W)。
    conf : dict
        连续性检测配置（gray_threshold_lte / edge_height / … 等）。

    Returns
    -------
    dict
        is_continuous : bool
        top_ends / bottom_ends / matches / …（来自 core 层）
    """
    _score, details = detect_pattern_continuity(image, conf)
    return {
        "is_continuous": details.get("is_continuous", False),
        **details,
    }
