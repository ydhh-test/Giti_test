"""
纵向细沟 core 算法测试说明。

这些测试只验证算法层是否能从 128×128 小图中提取纵向细沟特征，不验证规则层打分。
测试图像使用白底黑色竖条合成，便于明确期望的细沟数量、中心位置和边缘过滤行为。
同时覆盖调试模式输出和输入异常，确保算法边界清晰、调用失败时使用项目异常类直接暴露问题。
"""

import numpy as np
import pytest

from src.common.exceptions import InputDataError, InputTypeError
from src.core import longitudinal_groove as lg
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


class TestLongitudinalGrooveCoverageBranches:
    """补齐纵向细沟模块的边界与分支覆盖。"""

    def test_input_type_branches_are_raised(self):
        """输入类型分支应抛出项目异常。"""
        image = make_small_image_with_grooves([64])

        with pytest.raises(InputTypeError):
            detect_longitudinal_grooves(image, 123)  # type: ignore[arg-type]

        with pytest.raises(InputTypeError):
            detect_longitudinal_grooves(image, "center", is_debug=1)  # type: ignore[arg-type]

    def test_input_relation_branches_are_raised(self):
        """参数关系约束分支应抛出 InputDataError。"""
        image = make_small_image_with_grooves([64])

        with pytest.raises(InputDataError):
            detect_longitudinal_grooves(image, "center", min_width_px=5, max_width_px=4)

        with pytest.raises(InputDataError):
            detect_longitudinal_grooves(image, "center", min_width_px=5, narrow_cluster_px=4)

        with pytest.raises(InputDataError):
            detect_longitudinal_grooves(image, "center", max_angle_deg=85)

    def test_positive_number_and_int_validators_branches(self):
        """数值验证函数的类型和范围分支。"""
        image = make_small_image_with_grooves([64])

        with pytest.raises(InputTypeError):
            detect_longitudinal_grooves(image, "center", nominal_width_px=True)  # type: ignore[arg-type]

        with pytest.raises(InputDataError):
            detect_longitudinal_grooves(image, "center", nominal_width_px=0)

        with pytest.raises(InputTypeError):
            detect_longitudinal_grooves(image, "center", min_width_px=1.5)  # type: ignore[arg-type]

        with pytest.raises(InputTypeError):
            detect_longitudinal_grooves(image, "center", edge_margin_px=1.5)  # type: ignore[arg-type]

        with pytest.raises(InputDataError):
            detect_longitudinal_grooves(image, "center", edge_margin_px=-1)

    def test_split_row_data_by_angle_handles_empty_and_single(self):
        """轨迹切分需覆盖空输入与单元素输入分支。"""
        assert lg._split_row_data_by_angle([], max_angle_deg=30.0) == []

        single = [(10, 30.0, 4.0)]
        assert lg._split_row_data_by_angle(single, max_angle_deg=30.0) == [single]

    def test_split_row_data_by_angle_splits_on_large_tilt(self):
        """当相邻行偏转角超阈值时应切分轨迹。"""
        row_data = [
            (0, 10.0, 4.0),
            (1, 10.0, 4.0),
            (2, 40.0, 4.0),
            (3, 40.0, 4.0),
        ]

        segments = lg._split_row_data_by_angle(row_data, max_angle_deg=10.0, smooth_half_window=0)

        assert len(segments) == 2
        assert segments[0] == row_data[:2]
        assert segments[1] == row_data[2:]

    def test_build_groove_tracks_covers_gap_finish_and_candidate_skip(self):
        """覆盖轨迹超 gap 完结与候选冲突跳过分支。"""
        all_row_clusters = [
            (0, [(10, 10), (20, 20)]),
            (1, [(11, 11)]),
            (10, [(12, 12)]),
        ]

        tracks = lg._build_groove_tracks(all_row_clusters, max_dx=20.0, max_gap_rows=5)

        assert len(tracks) >= 2
        assert any(len(track) >= 2 for track in tracks)

    def test_split_columns_into_clusters_splits_discontinuous_columns(self):
        """同一行列索引出现间断时应拆分成多个簇。"""
        component_columns = np.array([0, 1, 2, 7, 8], dtype=np.int32)

        clusters = lg._split_columns_into_clusters(component_columns, left_offset=2)

        assert clusters == [(2, 4), (9, 10)]

    def test_validate_segment_branches(self):
        """候选段校验覆盖空段、过短和宽度越界分支。"""
        assert lg._validate_segment([], min_width_px=3, max_width_px=12, min_segment_length_px=2) is None

        too_short = [(0, 10.0, 4.0)]
        assert lg._validate_segment(too_short, min_width_px=3, max_width_px=12, min_segment_length_px=2) is None

        too_wide = [(0, 10.0, 20.0), (1, 10.0, 20.0), (2, 10.0, 20.0)]
        assert lg._validate_segment(too_wide, min_width_px=3, max_width_px=12, min_segment_length_px=2) is None

    def test_dedupe_segments_merges_overlapped_segments(self):
        """横向接近且纵向重叠超过阈值的段应被合并。"""
        raw_segments = [
            (10.0, 3.0, 0, 10),
            (11.0, 4.0, 2, 8),
        ]

        deduped = lg._dedupe_segments(raw_segments, dedup_distance_px=5.0)

        assert len(deduped) == 1
        merged_center, merged_width, merged_first_row, merged_last_row = deduped[0]
        assert merged_center == pytest.approx(10.5)
        assert merged_width == pytest.approx(4.0)
        assert merged_first_row == 0
        assert merged_last_row == 10

    def test_analyze_vertical_lines_skips_short_component(self):
        """连通域高度不足时应被直接跳过。"""
        binary = np.zeros((32, 32), dtype=np.uint8)
        binary[10:14, 16] = 255

        positions, count, line_mask, widths = lg._analyze_vertical_lines(
            binary=binary,
            min_width_px=1,
            narrow_cluster_px=3,
            edge_margin_px=0,
            min_segment_length_px=12,
            max_angle_deg=30.0,
            max_width_px=12,
            dedup_distance_px=8.0,
        )

        assert positions == []
        assert count == 0
        assert widths == []
        assert int(line_mask.sum()) == 0

    def test_analyze_vertical_lines_continue_on_empty_row_cluster(self, monkeypatch: pytest.MonkeyPatch):
        """当组件行列为空时应走 continue 分支并且不产出细沟。"""
        binary = np.zeros((32, 32), dtype=np.uint8)
        binary[2:28, 15:18] = 255

        original_where = lg.np.where

        def fake_where(_condition):
            return (np.array([], dtype=np.int64),)

        monkeypatch.setattr(lg.np, "where", fake_where)
        try:
            positions, count, line_mask, widths = lg._analyze_vertical_lines(
                binary=binary,
                min_width_px=1,
                narrow_cluster_px=3,
                edge_margin_px=0,
                min_segment_length_px=5,
                max_angle_deg=30.0,
                max_width_px=12,
                dedup_distance_px=8.0,
            )
        finally:
            monkeypatch.setattr(lg.np, "where", original_where)

        assert positions == []
        assert count == 0
        assert widths == []
        assert int(line_mask.sum()) == 0

    def test_analyze_vertical_lines_continue_on_rejected_segment(self):
        """当候选段宽度不满足约束时应跳过，不计入结果。"""
        binary = np.zeros((64, 64), dtype=np.uint8)
        binary[8:56, 32] = 255

        positions, count, line_mask, widths = lg._analyze_vertical_lines(
            binary=binary,
            min_width_px=3,
            narrow_cluster_px=12,
            edge_margin_px=0,
            min_segment_length_px=8,
            max_angle_deg=30.0,
            max_width_px=12,
            dedup_distance_px=8.0,
        )

        assert positions == []
        assert count == 0
        assert widths == []
        assert int(line_mask.sum()) == 0
