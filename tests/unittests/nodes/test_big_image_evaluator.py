from __future__ import annotations

import pytest

from src.common.exceptions import InputDataError
from src.models.enums import ImageFormatEnum, ImageModeEnum, LevelEnum, RegionEnum, SourceTypeEnum
from src.models.image_models import BigImage, ImageBiz, ImageMeta, SmallImage
from src.models.rule_models import Rule8Config, Rule8Feature, Rule8Score, Rule13Config, Rule13Feature, Rule13Score
from src.models.tire_struct import TireStruct
from src.nodes.big_image_evaluator import evaluate_big_image


def make_meta(width: int = 10, height: int = 20) -> ImageMeta:
    return ImageMeta(
        width=width,
        height=height,
        channels=3,
        mode=ImageModeEnum.RGB,
        format=ImageFormatEnum.PNG,
        size=5,
    )


def make_small_image() -> SmallImage:
    return SmallImage(
        image_base64="data:image/png;base64,small",
        meta=make_meta(),
        biz=ImageBiz(level=LevelEnum.SMALL, region=RegionEnum.CENTER),
    )


def make_big_image() -> BigImage:
    return BigImage(
        image_base64="data:image/png;base64,big",
        meta=make_meta(width=40),
        biz=ImageBiz(level=LevelEnum.BIG, source_type=SourceTypeEnum.CONCAT),
    )


class FakeRuleRunner:
    calls = []

    @classmethod
    def reset(cls) -> None:
        cls.calls = []

    @staticmethod
    def exec_feature(image, config):
        FakeRuleRunner.calls.append(("feature", image.image_base64, config.name))
        if config.name == "rule8":
            return Rule8Feature(num_transverse_grooves=3)
        if config.name == "rule13":
            return Rule13Feature(land_ratio=0.2)
        raise AssertionError(f"unexpected feature config {config.name}")

    @staticmethod
    def exec_score(config, feature):
        FakeRuleRunner.calls.append(("score", config.name, feature.name))
        if config.name == "rule8":
            return Rule8Score(score=3)
        if config.name == "rule13":
            return Rule13Score(score=2)
        raise AssertionError(f"unexpected score config {config.name}")


def test_evaluate_big_image_writes_single_big_image_evaluation_only(monkeypatch):
    """验证大图评估节点只处理 big_image，并按 Node4 顺序写入 rule8、rule13。"""
    FakeRuleRunner.reset()
    monkeypatch.setattr("src.nodes.base.RuleRunner", FakeRuleRunner)
    small_images = [make_small_image()]
    tire = TireStruct(
        small_images=small_images,
        big_image=make_big_image(),
        rules_config=[
            Rule13Config(land_ratio_min=0.1, land_ratio_max=0.5),
            Rule8Config(groove_width_center=1, groove_width_side=1),
        ],
    )

    result = evaluate_big_image(tire)

    assert result.flag is True
    assert result.err_msg is None
    assert result.small_images == small_images
    assert [rule.name for rule in result.big_image.evaluation.rules] == ["rule8", "rule13"]
    assert result.big_image.evaluation.current_score == 5
    assert [call[0] for call in FakeRuleRunner.calls] == ["feature", "score", "feature", "score"]


def test_evaluate_big_image_raises_input_error_when_big_image_missing():
    """验证缺少 big_image 时，大图评估节点抛出 InputDataError。"""
    tire = TireStruct(
        small_images=[make_small_image()],
        rules_config=[Rule8Config(groove_width_center=1, groove_width_side=1)],
    )

    with pytest.raises(InputDataError, match="big_image is required"):
        evaluate_big_image(tire)
