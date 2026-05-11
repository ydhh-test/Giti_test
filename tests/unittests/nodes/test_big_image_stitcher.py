import pytest

from src.nodes.big_image_stitcher import stitch_big_image


def test_stitch_big_image_placeholder_raises_not_implemented():
    """验证大图拼接节点当前仍是占位实现，会明确抛出 NotImplementedError。"""
    with pytest.raises(NotImplementedError, match="Big image stitcher placeholder"):
        stitch_big_image(input_data={})
