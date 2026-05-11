import pytest

from src.nodes.stitch_scheme_generator import generate_stitch_scheme


def test_generate_stitch_scheme_placeholder_raises_not_implemented():
    """验证拼接方案生成节点当前仍是占位实现，会明确抛出 NotImplementedError。"""
    with pytest.raises(NotImplementedError, match="Stitch scheme generator placeholder"):
        generate_stitch_scheme(input_data={})
