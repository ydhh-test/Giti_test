"""
纵向细沟 core 算法测试说明。

这些测试只验证算法层是否能从 128×128 小图中提取纵向细沟特征，不验证规则层打分。
测试图像使用白底黑色竖条合成，便于明确期望的细沟数量、中心位置和边缘过滤行为。
同时覆盖调试模式输出和输入异常，确保算法边界清晰、调用失败时使用项目异常类直接暴露问题。
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

from src.common.exceptions import InputDataError, InputTypeError
from src.core import longitudinal_groove as lg
from src.core.longitudinal_groove import detect_longitudinal_grooves


IMAGE_SIZE = 128
DATASET_ROOT = Path(__file__).parents[2] / "datasets" / "task_longitudinal_groove_vis"
DEBUG_OUTPUT_ROOT = Path(__file__).parents[3] / ".results" / "task_longitudinal_groove_vis" / "rule11"
REAL_IMAGE_PATHS = [
    DATASET_ROOT / "center_inf" / "0.png",
    DATASET_ROOT / "center_inf" / "2.png",
    DATASET_ROOT / "center_inf" / "4.png",
    DATASET_ROOT / "side_inf" / "1.png",
    DATASET_ROOT / "side_inf" / "3.png",
]


def make_small_image_with_grooves(center_columns: list[int], line_width: int = 4) -> np.ndarray:
    image = np.full((IMAGE_SIZE, IMAGE_SIZE, 3), 255, dtype=np.uint8)
    half_width = line_width // 2
    for center_column in center_columns:
        start_column = max(0, center_column - half_width)
        end_column = min(IMAGE_SIZE, start_column + line_width)
        image[12:116, start_column:end_column] = 0
    return image


def save_debug_image_like_dev(image_path: Path, debug_image: np.ndarray) -> Path:
    image_group = "center" if image_path.parent.name == "center_inf" else "side"
    output_dir = DEBUG_OUTPUT_ROOT / image_group
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{image_path.stem}_debug.png"
    success, buffer = cv2.imencode(".png", debug_image)
    assert success
    buffer.tofile(str(output_path))
    return output_path


class TestDetectLongitudinalGrooves:
    """纵向细沟 core 算法测试。"""

    @pytest.mark.parametrize("image_path", REAL_IMAGE_PATHS, ids=lambda path: path.name)
    def test_real_image_dataset_can_run_detector(self, image_path: Path):
        """dev 迁移来的真实小图应可被读取，并能跑通检测器。"""
        assert image_path.exists()

        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        assert image is not None
        assert image.shape == (IMAGE_SIZE, IMAGE_SIZE, 3)

        groove_count, groove_positions_px, groove_widths_px, line_mask, debug_image = detect_longitudinal_grooves(image, is_debug=True)

        assert groove_count == len(groove_positions_px) == len(groove_widths_px)
        assert all(0 <= position < IMAGE_SIZE for position in groove_positions_px)
        assert all(width > 0 for width in groove_widths_px)
        assert line_mask is not None
        assert line_mask.shape == (IMAGE_SIZE, IMAGE_SIZE)
        assert debug_image is not None
        assert debug_image.shape == image.shape

        debug_output_path = save_debug_image_like_dev(image_path, debug_image)
        assert debug_output_path.exists()
        saved_debug_image = cv2.imread(str(debug_output_path), cv2.IMREAD_COLOR)
        assert saved_debug_image is not None
        assert saved_debug_image.shape == image.shape

    def test_image_with_two_grooves_detects_two_lines(self):
        """小图中的两条纵向细沟应被完整检测出来。"""
        image = make_small_image_with_grooves([40, 86])

        groove_count, groove_positions_px, _groove_widths_px, line_mask, debug_image = detect_longitudinal_grooves(image)

        assert groove_count == 2
        assert len(groove_positions_px) == 2
        assert np.allclose(groove_positions_px, [39.5, 85.5], atol=2.0)
        assert line_mask is None
        assert debug_image is None

    def test_two_grooves_only_reports_features(self):
        """小图中出现两条纵向细沟时，算法只报告特征，不在 core 层扣分。"""
        image = make_small_image_with_grooves([40, 86])

        groove_count, _groove_positions_px, groove_widths_px, _line_mask, _debug_image = detect_longitudinal_grooves(image)

        assert groove_count == 2
        assert len(groove_widths_px) == 2

    def test_edge_residual_is_ignored(self):
        """靠左边缘的主沟残留应被边缘忽略参数过滤。"""
        image = make_small_image_with_grooves([5])

        groove_count, groove_positions_px, groove_widths_px, _line_mask, _debug_image = detect_longitudinal_grooves(image)

        assert groove_count == 0
        assert groove_positions_px == []
        assert groove_widths_px == []

    def test_debug_mode_returns_mask_and_debug_image(self):
        """is_debug=True 时应返回纵向细沟掩码和调试标注图。"""
        image = make_small_image_with_grooves([64])

        groove_count, _groove_positions_px, _groove_widths_px, line_mask, debug_image = detect_longitudinal_grooves(image, is_debug=True)

        assert groove_count == 1
        assert line_mask is not None
        assert line_mask.shape == (IMAGE_SIZE, IMAGE_SIZE)
        assert debug_image is not None
        assert debug_image.shape == image.shape

    def test_non_bgr_image_raises_input_data_error(self):
        """非 BGR 图像数组应直接抛出 InputDataError。"""
        image = np.full((IMAGE_SIZE, IMAGE_SIZE), 255, dtype=np.uint8)

        with pytest.raises(InputDataError) as exc_info:
            detect_longitudinal_grooves(image)

        assert "shape (H, W, 3)" in str(exc_info.value)

    def test_non_array_image_raises_input_type_error(self):
        """非 ndarray 图像输入应直接抛出 InputTypeError。"""
        with pytest.raises(InputTypeError) as exc_info:
            detect_longitudinal_grooves(None)

        assert "image" in str(exc_info.value)

    def test_invalid_pixel_parameter_raises_input_data_error(self):
        """像素阈值参数不合理时应直接抛出 InputDataError。"""
        image = make_small_image_with_grooves([64])

        with pytest.raises(InputDataError) as exc_info:
            detect_longitudinal_grooves(image, min_width_px=0)

        assert "min_width_px" in str(exc_info.value)


class TestLongitudinalGrooveCoverageBranches:
    """补齐纵向细沟模块的边界与分支覆盖。"""

    def test_input_type_branches_are_raised(self):
        """输入类型分支应抛出项目异常。"""
        image = make_small_image_with_grooves([64])

        with pytest.raises(InputTypeError):
            detect_longitudinal_grooves(image, is_debug=1)  # type: ignore[arg-type]

    def test_input_relation_branches_are_raised(self):
        """参数关系约束分支应抛出 InputDataError。"""
        image = make_small_image_with_grooves([64])

        with pytest.raises(InputDataError):
            detect_longitudinal_grooves(image, min_width_px=5, max_width_px=4)

        with pytest.raises(InputDataError):
            detect_longitudinal_grooves(image, min_width_px=5, narrow_cluster_px=4)

        with pytest.raises(InputDataError):
            detect_longitudinal_grooves(image, max_angle_deg=85)

    def test_positive_number_and_int_validators_branches(self):
        """数值验证函数的类型和范围分支。"""
        image = make_small_image_with_grooves([64])

        with pytest.raises(InputTypeError):
            detect_longitudinal_grooves(image, nominal_width_px=True)  # type: ignore[arg-type]

        with pytest.raises(InputDataError):
            detect_longitudinal_grooves(image, nominal_width_px=0)

        with pytest.raises(InputTypeError):
            detect_longitudinal_grooves(image, min_width_px=1.5)  # type: ignore[arg-type]

        with pytest.raises(InputTypeError):
            detect_longitudinal_grooves(image, edge_margin_px=1.5)  # type: ignore[arg-type]

        with pytest.raises(InputDataError):
            detect_longitudinal_grooves(image, edge_margin_px=-1)

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
