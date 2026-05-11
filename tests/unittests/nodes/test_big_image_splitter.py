import pytest

from src.nodes.big_image_splitter import split_big_image


def test_split_big_image_placeholder_raises_not_implemented():
    """验证大图拆分节点当前仍是占位实现，会明确抛出 NotImplementedError。"""
    with pytest.raises(NotImplementedError, match="Big image splitter placeholder"):
        split_big_image(input_data={})
