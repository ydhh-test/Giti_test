from __future__ import annotations

import numpy as np
import pytest

from src.common.exceptions import InputDataError, InputTypeError
from src.models.enums import ImageFormatEnum, ImageModeEnum, LevelEnum, RegionEnum, SourceTypeEnum
from src.models.image_models import BigImage, ImageBiz, ImageMeta, SmallImage
from src.models.rule_models import Rule6Feature, Rule11Config, Rule11Feature, Rule11Score
from src.rules.executors.rule11 import Rule11Executor
from src.utils.image_utils import ndarray_to_base64


IMAGE_SIZE = 128


def make_rule11_config(
    *,
    groove_width: float = 4.0,
    min_width_offset_px: int = 1,
    edge_margin_ratio: float = 0.1,
    min_segment_length_ratio: float = 0.125,
    max_angle_from_vertical: float = 30.0,
    max_count_center: int = 3,
    max_count_side: int = 2,
) -> Rule11Config:
    return Rule11Config(
        groove_width=groove_width,
        min_width_offset_px=min_width_offset_px,
        edge_margin_ratio=edge_margin_ratio,
        min_segment_length_ratio=min_segment_length_ratio,
        max_angle_from_vertical=max_angle_from_vertical,
        max_count_center=max_count_center,
        max_count_side=max_count_side,
    )


def make_image_with_grooves(center_columns: list[int], width: int = IMAGE_SIZE, height: int = IMAGE_SIZE) -> np.ndarray:
    image = np.full((height, width, 3), 255, dtype=np.uint8)
    half_width = 2
    for center_column in center_columns:
        start_column = max(0, center_column - half_width)
        end_column = min(width, start_column + 4)
        image[12: height - 12, start_column:end_column] = 0
    return image


def make_meta(image: np.ndarray) -> ImageMeta:
    height, width = image.shape[:2]
    return ImageMeta(
        width=width,
        height=height,
        channels=3,
        mode=ImageModeEnum.RGB,
        format=ImageFormatEnum.PNG,
        size=1,
    )


def make_small_image(image: np.ndarray, region: RegionEnum | None = RegionEnum.CENTER) -> SmallImage:
    source_type = SourceTypeEnum.ORIGINAL if region is not None else SourceTypeEnum.CONCAT
    return SmallImage(
        image_base64=ndarray_to_base64(image),
        meta=make_meta(image),
        biz=ImageBiz(level=LevelEnum.SMALL, region=region, source_type=source_type),
    )


def make_big_image(image: np.ndarray) -> BigImage:
    return BigImage(
        image_base64=ndarray_to_base64(image),
        meta=make_meta(image),
        biz=ImageBiz(level=LevelEnum.BIG, source_type=SourceTypeEnum.CONCAT),
    )


def test_exec_feature_detects_longitudinal_grooves_from_small_image():
    """Rule11 特征提取应解码小图并返回检测数量和区域。"""
    image = make_image_with_grooves([40, 86])
    small_image = make_small_image(image, RegionEnum.CENTER)

    feature = Rule11Executor().exec_feature(small_image, make_rule11_config())

    rst = feature
    expect_rst = Rule11Feature(
        num_longitudinal_grooves=2,
        region=RegionEnum.CENTER,
    )
    assert rst == expect_rst


def test_exec_feature_maps_config_to_detector_parameters(monkeypatch):
    """Rule11 应把配置中的比例和宽度字段显式转换为 core 算法参数。"""
    calls = []

    def fake_detect_longitudinal_grooves(image_array, **kwargs):
        calls.append({"shape": image_array.shape, **kwargs})
        return 7, [], [], None, None

    monkeypatch.setattr(
        "src.rules.executors.rule11.detect_longitudinal_grooves",
        fake_detect_longitudinal_grooves,
    )
    image = np.full((40, 80, 3), 255, dtype=np.uint8)
    small_image = make_small_image(image, RegionEnum.SIDE)
    config = make_rule11_config(
        groove_width=5.0,
        min_width_offset_px=1,
        edge_margin_ratio=0.1,
        min_segment_length_ratio=0.25,
        max_angle_from_vertical=15.0,
    )

    feature = Rule11Executor().exec_feature(small_image, config)

    rst = {
        "feature": feature,
        "calls": calls,
    }
    expect_rst = {
        "feature": Rule11Feature(
            num_longitudinal_grooves=7,
            region=RegionEnum.SIDE,
        ),
        "calls": [
            {
                "shape": (40, 80, 3),
                "nominal_width_px": 5.0,
                "min_width_px": 4,
                "edge_margin_px": 8,
                "min_segment_length_px": 10,
                "max_angle_deg": 15.0,
            }
        ],
    }
    assert rst == expect_rst


@pytest.mark.parametrize(
    ("region", "count", "expected_score"),
    [
        (RegionEnum.CENTER, 3, 4),
        (RegionEnum.CENTER, 4, 0),
        (RegionEnum.SIDE, 2, 4),
        (RegionEnum.SIDE, 3, 0),
    ],
)
def test_exec_score_uses_region_specific_count_limit(region: RegionEnum, count: int, expected_score: int):
    """Rule11 评分应按小图区域选择 center/side 数量上限。"""
    score = Rule11Executor().exec_score(
        make_rule11_config(max_count_center=3, max_count_side=2),
        Rule11Feature(num_longitudinal_grooves=count, region=region),
    )

    rst = score
    expect_rst = Rule11Score(score=expected_score)
    assert rst == expect_rst


def test_exec_feature_rejects_non_small_image():
    """Rule11 是小图规则，不能直接接收 BigImage。"""
    image = make_image_with_grooves([40])

    with pytest.raises(InputTypeError, match="SmallImage"):
        Rule11Executor().exec_feature(make_big_image(image), make_rule11_config())


def test_exec_feature_rejects_missing_region():
    """Rule11 评分需要 center/side 区域信息。"""
    image = make_image_with_grooves([40])

    with pytest.raises(InputDataError, match="image.biz.region"):
        Rule11Executor().exec_feature(make_small_image(image, None), make_rule11_config())


def test_exec_score_rejects_wrong_feature_type():
    """Rule11 打分只接受 Rule11Feature。"""
    with pytest.raises(InputTypeError, match="Rule11Feature"):
        Rule11Executor().exec_score(make_rule11_config(), Rule6Feature(is_continuous=True))


def test_exec_score_rejects_invalid_feature_region():
    """绕过模型校验构造的非法 region 应在评分入口被拒绝。"""
    feature = Rule11Feature.model_construct(num_longitudinal_grooves=1, region=None)

    with pytest.raises(InputDataError, match="feature.region"):
        Rule11Executor().exec_score(make_rule11_config(), feature)
