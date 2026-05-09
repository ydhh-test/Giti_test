"""
纵向细沟 core 算法测试说明。

这些测试只验证算法层是否能从 128×128 小图中提取纵向细沟特征，不验证规则层打分。
测试图像使用白底黑色竖条合成，便于明确期望的细沟数量、中心位置和边缘过滤行为。
同时覆盖调试模式输出和输入异常，确保算法边界清晰、调用失败时使用项目异常类直接暴露问题。
"""

import numpy as np
import pytest

from src.common.exceptions import InputDataError, InputTypeError
from src.core.longitudinal_groove import detect_longitudinal_grooves


IMAGE_SIZE = 128


def make_small_image_with_grooves(center_columns: list[int], line_width: int = 4) -> np.ndarray:
    image = np.full((IMAGE_SIZE, IMAGE_SIZE, 3), 255, dtype=np.uint8)
    half_width = line_width // 2
    for center_column in center_columns:
        start_column = max(0, center_column - half_width)
        end_column = min(IMAGE_SIZE, start_column + line_width)
        image[12:116, start_column:end_column] = 0
    return image


class TestDetectLongitudinalGrooves:
    """纵向细沟 core 算法测试。"""

    def test_center_image_with_two_grooves_detects_two_lines(self):
        """center 小图中的两条纵向细沟应被完整检测出来。"""
        image = make_small_image_with_grooves([40, 86])

        result = detect_longitudinal_grooves(image, "center")

        assert result.image_type == "center"
        assert result.groove_count == 2
        assert len(result.groove_positions_px) == 2
        assert np.allclose(result.groove_positions_px, [39.5, 85.5], atol=2.0)
        assert result.line_mask is None
        assert result.debug_image is None

    def test_side_image_with_two_grooves_only_reports_features(self):
        """side 小图中出现两条纵向细沟时，算法只报告特征，不在 core 层扣分。"""
        image = make_small_image_with_grooves([40, 86])

        result = detect_longitudinal_grooves(image, "side")

        assert result.image_type == "side"
        assert result.groove_count == 2
        assert len(result.groove_widths_px) == 2

    def test_edge_residual_is_ignored(self):
        """靠左边缘的主沟残留应被边缘忽略参数过滤。"""
        image = make_small_image_with_grooves([5])

        result = detect_longitudinal_grooves(image, "side")

        assert result.groove_count == 0
        assert result.groove_positions_px == []
        assert result.groove_widths_px == []

    def test_debug_mode_returns_mask_and_debug_image(self):
        """is_debug=True 时应返回纵向细沟掩码和调试标注图。"""
        image = make_small_image_with_grooves([64])

        result = detect_longitudinal_grooves(image, "center", is_debug=True)

        assert result.groove_count == 1
        assert result.line_mask is not None
        assert result.line_mask.shape == (IMAGE_SIZE, IMAGE_SIZE)
        assert result.debug_image is not None
        assert result.debug_image.shape == image.shape

    def test_invalid_image_type_raises_input_data_error(self):
        """非法 image_type 应直接抛出 InputDataError。"""
        image = make_small_image_with_grooves([64])

        with pytest.raises(InputDataError) as exc_info:
            detect_longitudinal_grooves(image, "middle")

        assert "image_type" in str(exc_info.value)

    def test_non_bgr_image_raises_input_data_error(self):
        """非 BGR 图像数组应直接抛出 InputDataError。"""
        image = np.full((IMAGE_SIZE, IMAGE_SIZE), 255, dtype=np.uint8)

        with pytest.raises(InputDataError) as exc_info:
            detect_longitudinal_grooves(image, "center")

        assert "shape (H, W, 3)" in str(exc_info.value)

    def test_non_array_image_raises_input_type_error(self):
        """非 ndarray 图像输入应直接抛出 InputTypeError。"""
        with pytest.raises(InputTypeError) as exc_info:
            detect_longitudinal_grooves(None, "center")

        assert "image" in str(exc_info.value)

    def test_invalid_pixel_parameter_raises_input_data_error(self):
        """像素阈值参数不合理时应直接抛出 InputDataError。"""
        image = make_small_image_with_grooves([64])

        with pytest.raises(InputDataError) as exc_info:
            detect_longitudinal_grooves(image, "center", min_width_px=0)

        assert "min_width_px" in str(exc_info.value)
