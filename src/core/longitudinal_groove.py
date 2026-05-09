from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import cv2
import numpy as np

from src.common.exceptions import InputDataError, InputTypeError
from src.utils.logger import get_logger


ImageType = Literal["center", "side"]
RowData = list[tuple[int, float, float]]
Segment = tuple[float, float, int, int]

logger = get_logger(__name__)


@dataclass(frozen=True)
class LongitudinalGrooveDefaults:
    score: int = 4
    max_count: dict[str, int] = field(default_factory=lambda: {"center": 2, "side": 1})
    rib_label: dict[str, str] = field(default_factory=lambda: {"center": "RIB2/3/4", "side": "RIB1/5"})


_DEFAULTS = LongitudinalGrooveDefaults()


def detect_longitudinal_grooves(
    image: np.ndarray,
    image_type: str,
    groove_width_mm: float = 0.34,
    pixel_per_mm: float = 11.81,
    min_width_offset_px: int = 1,
    edge_margin_ratio: float = 0.10,
    min_segment_length_ratio: float = 0.12,
    max_angle_deg: float = 30.0,
    max_width_factor: float = 3.0,
) -> tuple[float | None, dict[str, Any]]:
    """Detect vertical grooves or sipes in a small BGR tire-pattern image.

    The migrated Rule 11 algorithm scores by counting dark near-vertical line
    segments. ``center`` images allow up to two lines, and ``side`` images allow
    up to one line. The function keeps the legacy return shape: ``(score,
    details)`` on success and ``(None, error_details)`` on failure.
    """
    try:
        normalized_image_type = _validate_inputs(image, image_type)
        logger.debug("Start longitudinal groove detection, image_type=%s", normalized_image_type)

        nominal_width_px = groove_width_mm * pixel_per_mm
        min_width_px = max(1, int(round(nominal_width_px)) - min_width_offset_px)
        max_width_px = max(int(round(nominal_width_px * max_width_factor)), min_width_px + 2)
        narrow_cluster_px = max(min_width_px + 1, int(round(nominal_width_px * 3)))
        dedup_distance_px = nominal_width_px * 2.0

        rib_type = _DEFAULTS.rib_label[normalized_image_type]
        max_count = _DEFAULTS.max_count[normalized_image_type]
        image_height, image_width = image.shape[:2]

        edge_margin_px = max(0, int(image_width * edge_margin_ratio))
        min_segment_length_px = max(1, int(np.ceil(image_width * min_segment_length_ratio)))

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred_image = cv2.GaussianBlur(gray_image, (3, 3), 0)
        binary_image = cv2.adaptiveThreshold(
            blurred_image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=31,
            C=5,
        )

        positions, groove_count, line_mask, widths = _analyze_vertical_lines(
            binary=binary_image,
            min_width_px=min_width_px,
            narrow_cluster_px=narrow_cluster_px,
            image_height=image_height,
            edge_margin_px=edge_margin_px,
            min_segment_length_px=min_segment_length_px,
            max_angle_deg=max_angle_deg,
            max_width_px=max_width_px,
            dedup_distance_px=dedup_distance_px,
        )

        score_value = _compute_score(groove_count, max_count, _DEFAULTS.score)
        is_valid = score_value > 0
        debug_image = _draw_debug_image(
            image=image,
            line_mask=line_mask,
            positions=positions,
            widths=widths,
            rib_type=rib_type,
            count=groove_count,
            max_count=max_count,
            is_valid=is_valid,
            score=score_value,
        )

        details: dict[str, Any] = {
            "rib_type": rib_type,
            "groove_count": groove_count,
            "groove_positions": positions,
            "groove_widths": widths,
            "is_valid": is_valid,
            "score": float(score_value),
            "line_mask": line_mask,
            "debug_image": debug_image,
        }
        logger.debug("Longitudinal groove detection finished, score=%.1f, valid=%s", score_value, is_valid)
        return float(score_value), details
    except Exception as exc:  # Keep legacy algorithm contract for rule callers.
        logger.error("Longitudinal groove detection failed: %s", exc)
        return None, {"err_msg": str(exc), "error_type": type(exc).__name__}


def _validate_inputs(image: np.ndarray, image_type: str) -> ImageType:
    if not isinstance(image, np.ndarray):
        raise InputTypeError("detect_longitudinal_grooves", "image", "np.ndarray", type(image).__name__)
    if image.ndim != 3 or image.shape[2] != 3:
        raise InputDataError("detect_longitudinal_grooves", "image", "expected BGR image with shape (H, W, 3)", image.shape)
    if not isinstance(image_type, str):
        raise InputTypeError("detect_longitudinal_grooves", "image_type", "str", type(image_type).__name__)

    normalized_image_type = image_type.strip().lower()
    if normalized_image_type not in _DEFAULTS.rib_label:
        raise InputDataError(
            "detect_longitudinal_grooves",
            "image_type",
            "must be one of ['center', 'side']",
            image_type,
        )
    return normalized_image_type  # type: ignore[return-value]


def _bridge_small_vertical_gaps(binary: np.ndarray, max_gap_px: int = 4) -> np.ndarray:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max_gap_px + 1))
    return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)


def _split_row_data_by_angle(
    row_data: RowData,
    max_angle_deg: float,
    smooth_half_window: int = 3,
) -> list[RowData]:
    if not row_data:
        return []
    if len(row_data) == 1:
        return [row_data]

    center_values = np.array([row_item[1] for row_item in row_data], dtype=np.float64)
    smoothed_centers = np.array(
        [
            center_values[max(0, index - smooth_half_window): min(len(row_data), index + smooth_half_window + 1)].mean()
            for index in range(len(row_data))
        ]
    )

    max_slope = float(np.tan(np.radians(max_angle_deg)))
    segments: list[RowData] = []
    segment_start = 0

    for row_index in range(1, len(row_data)):
        previous_row = row_data[row_index - 1][0]
        current_row = row_data[row_index][0]
        row_gap = max(1, current_row - previous_row)
        center_delta = abs(smoothed_centers[row_index] - smoothed_centers[row_index - 1])

        if center_delta > max_slope * row_gap:
            segments.append(row_data[segment_start:row_index])
            segment_start = row_index

    segments.append(row_data[segment_start:])
    return [segment for segment in segments if segment]


def _build_groove_tracks(
    all_row_clusters: list[tuple[int, list[tuple[int, int]]]],
    max_dx: float = 8.0,
    max_gap_rows: int = 5,
) -> list[RowData]:
    active_tracks: list[dict[str, Any]] = []
    finished_tracks: list[RowData] = []

    for row_index, clusters in all_row_clusters:
        cluster_info = [((start_col + end_col) / 2.0, float(end_col - start_col + 1)) for start_col, end_col in clusters]

        still_active: list[dict[str, Any]] = []
        for track in active_tracks:
            if row_index - track["last_row"] > max_gap_rows:
                finished_tracks.append(track["data"])
            else:
                still_active.append(track)
        active_tracks = still_active

        candidates: list[tuple[float, int, int]] = []
        for track_index, track in enumerate(active_tracks):
            for cluster_index, (center_x, _row_width) in enumerate(cluster_info):
                distance = abs(center_x - track["last_center_x"])
                if distance <= max_dx:
                    candidates.append((distance, track_index, cluster_index))
        candidates.sort()

        matched_tracks: set[int] = set()
        matched_clusters: set[int] = set()
        for _distance, track_index, cluster_index in candidates:
            if track_index in matched_tracks or cluster_index in matched_clusters:
                continue
            center_x, row_width = cluster_info[cluster_index]
            active_tracks[track_index]["data"].append((row_index, center_x, row_width))
            active_tracks[track_index]["last_row"] = row_index
            active_tracks[track_index]["last_center_x"] = center_x
            matched_tracks.add(track_index)
            matched_clusters.add(cluster_index)

        for cluster_index, (center_x, row_width) in enumerate(cluster_info):
            if cluster_index not in matched_clusters:
                active_tracks.append(
                    {
                        "data": [(row_index, center_x, row_width)],
                        "last_row": row_index,
                        "last_center_x": center_x,
                    }
                )

    for track in active_tracks:
        finished_tracks.append(track["data"])
    return finished_tracks


def _analyze_vertical_lines(
    binary: np.ndarray,
    min_width_px: int,
    narrow_cluster_px: int,
    image_height: int,
    edge_margin_px: int = 0,
    min_segment_length_px: int = 1,
    max_angle_deg: float = 30.0,
    max_width_px: int = 12,
    dedup_distance_px: float = 8.0,
) -> tuple[list[float], int, np.ndarray, list[float]]:
    working_binary = binary.copy()
    image_width = binary.shape[1]

    if edge_margin_px > 0:
        working_binary[:, :edge_margin_px] = 0
        working_binary[:, max(0, image_width - edge_margin_px):] = 0

    bridged_binary = _bridge_small_vertical_gaps(working_binary, max_gap_px=4)
    if 0 < max_angle_deg < 85:
        max_tilt_vertical_span = int(min_width_px / np.tan(np.radians(max_angle_deg)))
    else:
        max_tilt_vertical_span = min_segment_length_px
    vertical_open_height = max(3, min(max_tilt_vertical_span, min_segment_length_px // 2))
    open_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_open_height))
    bridged_binary = cv2.morphologyEx(bridged_binary, cv2.MORPH_OPEN, open_kernel)

    label_count, labels, stats, _centroids = cv2.connectedComponentsWithStats(
        (bridged_binary > 0).astype(np.uint8), connectivity=8
    )

    line_mask = np.zeros_like(binary)
    raw_segments: list[Segment] = []

    for label_id in range(1, label_count):
        left = int(stats[label_id, cv2.CC_STAT_LEFT])
        top = int(stats[label_id, cv2.CC_STAT_TOP])
        bbox_width = int(stats[label_id, cv2.CC_STAT_WIDTH])
        bbox_height = int(stats[label_id, cv2.CC_STAT_HEIGHT])

        if bbox_height < min_segment_length_px:
            continue

        all_row_clusters: list[tuple[int, list[tuple[int, int]]]] = []
        for row_index in range(top, top + bbox_height):
            component_columns = np.where(labels[row_index, left: left + bbox_width + 1] == label_id)[0]
            if len(component_columns) == 0:
                continue

            row_clusters = _split_columns_into_clusters(component_columns, left)
            narrow_clusters = [
                (start_col, end_col)
                for start_col, end_col in row_clusters
                if (end_col - start_col + 1) <= narrow_cluster_px
            ]
            if narrow_clusters:
                all_row_clusters.append((row_index, narrow_clusters))

        if not all_row_clusters:
            continue

        tracks = _build_groove_tracks(all_row_clusters, max_dx=narrow_cluster_px, max_gap_rows=5)
        for track_data in tracks:
            for segment in _split_row_data_by_angle(track_data, max_angle_deg):
                accepted_segment = _validate_segment(
                    segment=segment,
                    min_width_px=min_width_px,
                    max_width_px=max_width_px,
                    min_segment_length_px=min_segment_length_px,
                )
                if accepted_segment is None:
                    continue

                center_x, mean_width, first_row, last_row = accepted_segment
                _paint_segment_mask(line_mask, segment)
                raw_segments.append((center_x, mean_width, first_row, last_row))

    deduped_segments = _dedupe_segments(raw_segments, dedup_distance_px)
    positions = [position for position, _width, _first_row, _last_row in deduped_segments]
    widths = [width for _position, width, _first_row, _last_row in deduped_segments]
    return positions, len(deduped_segments), line_mask, widths


def _split_columns_into_clusters(component_columns: np.ndarray, left_offset: int) -> list[tuple[int, int]]:
    row_clusters: list[tuple[int, int]] = []
    cluster_start = int(component_columns[0])
    for column_index in range(1, len(component_columns)):
        if int(component_columns[column_index]) - int(component_columns[column_index - 1]) > 2:
            row_clusters.append((cluster_start + left_offset, int(component_columns[column_index - 1]) + left_offset))
            cluster_start = int(component_columns[column_index])
    row_clusters.append((cluster_start + left_offset, int(component_columns[-1]) + left_offset))
    return row_clusters


def _validate_segment(
    segment: RowData,
    min_width_px: int,
    max_width_px: int,
    min_segment_length_px: int,
) -> Segment | None:
    if not segment:
        return None

    first_row = segment[0][0]
    last_row = segment[-1][0]
    segment_height = last_row - first_row + 1
    if segment_height < min_segment_length_px:
        return None

    mean_width = float(np.mean([row_width for _row_index, _center_x, row_width in segment]))
    if mean_width < min_width_px or mean_width > max_width_px:
        return None

    center_x = float(np.mean([center_x for _row_index, center_x, _row_width in segment]))
    return center_x, mean_width, first_row, last_row


def _paint_segment_mask(line_mask: np.ndarray, segment: RowData) -> None:
    for row_index, center_x, row_width in segment:
        start_col = max(0, int(round(center_x - row_width / 2.0)))
        end_col = min(line_mask.shape[1] - 1, int(round(center_x + row_width / 2.0)))
        line_mask[row_index, start_col: end_col + 1] = 255


def _dedupe_segments(raw_segments: list[Segment], dedup_distance_px: float) -> list[Segment]:
    raw_segments.sort(key=lambda item: item[0])
    deduped_segments: list[Segment] = []

    for center_x, width, first_row, last_row in raw_segments:
        merged = False
        for segment_index, (existing_center_x, existing_width, existing_first_row, existing_last_row) in enumerate(deduped_segments):
            if abs(center_x - existing_center_x) >= dedup_distance_px:
                continue

            overlap = max(0, min(last_row, existing_last_row) - max(first_row, existing_first_row) + 1)
            min_span = min(last_row - first_row + 1, existing_last_row - existing_first_row + 1)
            if min_span > 0 and overlap / min_span > 0.5:
                deduped_segments[segment_index] = (
                    (existing_center_x + center_x) / 2.0,
                    max(existing_width, width),
                    min(existing_first_row, first_row),
                    max(existing_last_row, last_row),
                )
                merged = True
                break

        if not merged:
            deduped_segments.append((center_x, width, first_row, last_row))

    return deduped_segments


def _compute_score(count: int, max_count: int, max_score: int) -> int:
    return max_score if count <= max_count else 0


def _draw_debug_image(
    image: np.ndarray,
    line_mask: np.ndarray,
    positions: list[float],
    widths: list[float],
    rib_type: str,
    count: int,
    max_count: int,
    is_valid: bool,
    score: float,
) -> np.ndarray:
    debug_image = image.copy()
    overlay = np.zeros_like(debug_image)
    overlay[line_mask > 0] = (200, 100, 0)
    debug_image = cv2.addWeighted(debug_image, 0.7, overlay, 0.3, 0)

    image_height = debug_image.shape[0]
    line_color = (0, 255, 0) if is_valid else (0, 0, 255)
    for position in positions:
        center_col = int(round(position))
        cv2.line(debug_image, (center_col, 0), (center_col, image_height - 1), line_color, 1)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.35
    font_thickness = 1
    text_color = (255, 255, 255)
    background_color = (0, 0, 0)
    labels = [rib_type, f"L:{count}/{max_count} {'OK' if is_valid else 'NG'}", f"S:{score:.0f}"]
    text_y = 10
    for label in labels:
        (text_width, text_height), _baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
        cv2.rectangle(debug_image, (1, text_y - text_height - 1), (3 + text_width, text_y + 2), background_color, -1)
        cv2.putText(debug_image, label, (2, text_y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)
        text_y += text_height + 4

    return debug_image


__all__ = ["detect_longitudinal_grooves"]