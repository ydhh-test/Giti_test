# -*- coding: utf-8 -*-
"""
Rule 8 评分：横沟数量约束。
- RIB1/5 (center)：groove_count == 1 → max_score；否则 0
- RIB2/3/4 (side)：groove_count <= 1 → max_score；否则 0
"""


def score(groove_count: int, rib_type: str, max_score: int = 4) -> int:
    """
    Parameters
    ----------
    groove_count : int
        检测到的横沟数量（来自 features/rule_8_14）。
    rib_type : str
        "RIB1/5" 或 "RIB2/3/4"（来自 features/rule_8_14）。
    max_score : int
        满分，默认 4。
    """
    if rib_type == "RIB1/5":
        return max_score if groove_count == 1 else 0
    else:  # RIB2/3/4
        return max_score if groove_count <= 1 else 0
