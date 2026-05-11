from __future__ import annotations

import pytest

from src.common.exceptions import InputDataError
from src.models.enums import ImageFormatEnum, ImageModeEnum, LevelEnum, SourceTypeEnum
from src.models.image_models import BigImage, ImageBiz, ImageEvaluation, ImageMeta, RuleEvaluation
from src.models.rule_models import Rule8Config, Rule8Feature, Rule8Score
from src.nodes.geometry_scorer import score_geometry


def make_meta(width: int = 10, height: int = 20) -> ImageMeta:
    return ImageMeta(
        width=width,
        height=height,
        channels=3,
        mode=ImageModeEnum.RGB,
        format=ImageFormatEnum.PNG,
        size=5,
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
    def exec_score(config, feature):
        FakeRuleRunner.calls.append(("score", config.name, feature.name))
        return Rule8Score(score=3)


def test_score_geometry_recalculates_scores_without_exec_feature(monkeypatch):
    """验证几何评分节点接收大图并基于已有 feature 重算 score 和总分。"""
    FakeRuleRunner.reset()
    monkeypatch.setattr("src.nodes.geometry_scorer.RuleRunner", FakeRuleRunner)
    config = Rule8Config(groove_width_center=1, groove_width_side=1)
    feature = Rule8Feature(num_transverse_grooves=5)
    big_image = make_big_image()
    big_image.evaluation = ImageEvaluation(
        rules=[
            RuleEvaluation(
                name="rule8",
                config=config,
                feature=feature,
                score=Rule8Score(score=1),
            )
        ],
        current_score=1,
    )

    result = score_geometry(big_image, [config])

    assert result is big_image
    assert result.evaluation.get_rule("rule8").score == Rule8Score(score=3)
    assert result.evaluation.current_score == 3
    assert FakeRuleRunner.calls == [("score", "rule8", "rule8")]


def test_score_geometry_raises_input_error_when_feature_missing(monkeypatch):
    """验证几何评分节点发现目标 RuleEvaluation 缺少 feature 时会快速失败。"""
    FakeRuleRunner.reset()
    monkeypatch.setattr("src.nodes.geometry_scorer.RuleRunner", FakeRuleRunner)
    config = Rule8Config(groove_width_center=1, groove_width_side=1)
    big_image = make_big_image()
    big_image.evaluation = ImageEvaluation(
        rules=[RuleEvaluation(name="rule8", config=config)],
    )

    with pytest.raises(InputDataError, match="missing feature for rule8"):
        score_geometry(big_image, [config])
