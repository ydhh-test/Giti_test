# -*- coding: utf-8 -*-
"""
Rule 6_1 评分：节距纵向图案连续性。
输入：is_continuous（来自 features/rule_6_1）
输出：score（0 或 max_score）
"""


def score(is_continuous: bool, max_score: int = 10) -> int:
    """连续 → max_score；不连续 → 0。"""
    return max_score if is_continuous else 0
