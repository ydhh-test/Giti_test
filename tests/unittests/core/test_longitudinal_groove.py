import numpy as np

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
    """Rule 11 longitudinal groove core algorithm tests."""

    def test_center_image_with_two_grooves_scores_full(self):
        """Center small images allow up to two longitudinal grooves."""
        image = make_small_image_with_grooves([40, 86])

        score, details = detect_longitudinal_grooves(image, "center")

        assert score == 4.0
        assert details["score"] == 4.0
        assert details["is_valid"] is True
        assert details["rib_type"] == "RIB2/3/4"
        assert details["groove_count"] == 2
        assert len(details["groove_positions"]) == 2
        assert np.allclose(details["groove_positions"], [39.5, 85.5], atol=2.0)
        assert details["line_mask"].shape == (IMAGE_SIZE, IMAGE_SIZE)
        assert details["debug_image"].shape == image.shape

    def test_side_image_with_one_groove_scores_full(self):
        """Side small images allow one longitudinal groove."""
        image = make_small_image_with_grooves([64])

        score, details = detect_longitudinal_grooves(image, "side")

        assert score == 4.0
        assert details["is_valid"] is True
        assert details["rib_type"] == "RIB1/5"
        assert details["groove_count"] == 1

    def test_side_image_with_two_grooves_scores_zero(self):
        """Side small images fail when longitudinal groove count exceeds one."""
        image = make_small_image_with_grooves([40, 86])

        score, details = detect_longitudinal_grooves(image, "side")

        assert score == 0.0
        assert details["score"] == 0.0
        assert details["is_valid"] is False
        assert details["groove_count"] == 2

    def test_edge_residual_is_ignored(self):
        """Groove-like dark lines in the left edge margin are ignored."""
        image = make_small_image_with_grooves([5])

        score, details = detect_longitudinal_grooves(image, "side")

        assert score == 4.0
        assert details["is_valid"] is True
        assert details["groove_count"] == 0
        assert details["groove_positions"] == []

    def test_invalid_image_type_returns_input_data_error(self):
        """Invalid image_type preserves the legacy non-raising return contract."""
        image = make_small_image_with_grooves([64])

        score, details = detect_longitudinal_grooves(image, "middle")

        assert score is None
        assert details["error_type"] == "InputDataError"
        assert "image_type" in details["err_msg"]

    def test_non_bgr_image_returns_input_data_error(self):
        """Non-BGR image arrays return InputDataError details."""
        image = np.full((IMAGE_SIZE, IMAGE_SIZE), 255, dtype=np.uint8)

        score, details = detect_longitudinal_grooves(image, "center")

        assert score is None
        assert details["error_type"] == "InputDataError"
        assert "shape (H, W, 3)" in details["err_msg"]

    def test_non_array_image_returns_input_type_error(self):
        """Non-array image values return InputTypeError details."""
        score, details = detect_longitudinal_grooves(None, "center")

        assert score is None
        assert details["error_type"] == "InputTypeError"
        assert "image" in details["err_msg"]
