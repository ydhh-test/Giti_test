# -*- coding: utf-8 -*-

"""配置校验与质量检测"""

# Copyright © 2026. All rights reserved.

from src.utils.logger import get_logger

logger = get_logger(__name__)


def _validate_vertical_parts_to_keep(parts_to_keep, num_segments_to_remove):
    """
    校验vertical_parts_to_keep配置的有效性
    校验规则:
        1. 列表不能为空
        2. 列表值不能重复
        3. 列表值必须在有效范围内 [1, num_segments_to_remove+1]
        4. 必须至少包含一个side索引
        5. 必须至少包含一个center索引
    Args:
        parts_to_keep: 要保留的索引列表
        num_segments_to_remove: 主沟数量（3或4）

    Raises:
        ValueError: 校验失败时抛出
    """
    if not parts_to_keep:
        raise ValueError("vertical_parts_to_keep不能为空列表")

    if len(parts_to_keep) != len(set(parts_to_keep)):
        duplicates = [x for x in parts_to_keep if parts_to_keep.count(x) > 1]
        raise ValueError(f"vertical_parts_to_keep包含重复值: {set(duplicates)}")

    max_index = num_segments_to_remove + 1

    invalid_values = [x for x in parts_to_keep if x < 1 or x > max_index]
    if invalid_values:
        raise ValueError(
            f"vertical_parts_to_keep包含无效索引: {invalid_values} "
            f"(有效范围: 1~{max_index})"
        )

    if num_segments_to_remove == 4:
        side_indices = {1, 5}
        center_indices = {2, 3, 4}
    else:
        side_indices = {1, 4}
        center_indices = {2, 3}

    parts_set = set(parts_to_keep)

    if not (parts_set & side_indices):
        raise ValueError(
            f"vertical_parts_to_keep必须至少包含一个side部分 "
            f"(side索引: {sorted(side_indices)})"
        )

    if not (parts_set & center_indices):
        raise ValueError(
            f"vertical_parts_to_keep必须至少包含一个center部分 "
            f"(center索引: {sorted(center_indices)})"
        )
