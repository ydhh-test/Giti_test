# -*- coding: utf-8 -*-
"""
Rule 14 评分：钢片 & 横沟与其他线条交点数量约束。
intersection_count <= max_intersections → max_score；否则 0
"""


def score(
    intersection_count: int,
    max_intersections: int = 2,
    max_score: int = 2,
) -> int:
    """
    Parameters
    ----------
    intersection_count : int
        交叉点数量（来自 features/rule_8_14）。
    """
    return max_score if intersection_count <= max_intersections else 0
