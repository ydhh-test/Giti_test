# -*- coding: utf-8 -*-
"""
Rule 11 评分：纵向细沟 & 纵向钢片数量约束。
- center (RIB2/3/4)：count <= max_count_center → max_score；否则 0
- side   (RIB1/5)  ：count <= max_count_side   → max_score；否则 0
"""


def score(
    num_longitudinal_grooves: int,
    image_type: str,
    max_count_center: int = 2,
    max_count_side: int = 1,
    max_score: int = 4,
) -> int:
    limit = max_count_center if image_type == "center" else max_count_side
    return max_score if num_longitudinal_grooves <= limit else 0
