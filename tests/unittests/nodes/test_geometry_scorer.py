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


def test_score_geometry_updates_config_and_score_when_rules_config_changed(monkeypatch):
    """验证用户修改 rules_config 后，几何评分节点会更新 RuleEvaluation 的 config 和 score。"""
    FakeRuleRunner.reset()
    monkeypatch.setattr("src.nodes.geometry_scorer.RuleRunner", FakeRuleRunner)
    old_config = Rule8Config(groove_width_center=1, groove_width_side=1)
    new_config = Rule8Config(groove_width_center=2, groove_width_side=3)
    feature = Rule8Feature(num_transverse_grooves=5)
    big_image = make_big_image()
    big_image.evaluation = ImageEvaluation(
        rules=[
            RuleEvaluation(
                name="rule8",
                config=old_config,
                feature=feature,
                score=Rule8Score(score=1),
            )
        ],
        current_score=1,
    )

    result = score_geometry(big_image, [new_config])
    rule_evaluation = result.evaluation.get_rule("rule8")

    assert rule_evaluation.config is new_config
    assert rule_evaluation.feature is feature
    assert rule_evaluation.score == Rule8Score(score=3)
    assert result.evaluation.current_score == 3
    assert FakeRuleRunner.calls == [("score", "rule8", "rule8")]


def test_score_geometry_can_refresh_total_without_recalculating_rule_scores(monkeypatch):
    """验证几何评分节点可以只汇总已有 rule score，不重新计算每条规则评分。"""
    FakeRuleRunner.reset()
    monkeypatch.setattr("src.nodes.geometry_scorer.RuleRunner", FakeRuleRunner)
    config = Rule8Config(groove_width_center=1, groove_width_side=1)
    big_image = make_big_image()
    big_image.evaluation = ImageEvaluation(
        rules=[
            RuleEvaluation(
                name="rule8",
                config=config,
                feature=Rule8Feature(num_transverse_grooves=5),
                score=Rule8Score(score=4),
            )
        ],
        current_score=0,
    )

    result = score_geometry(big_image, [config], recalculate_rule_scores=False)

    assert result.evaluation.get_rule("rule8").score == Rule8Score(score=4)
    assert result.evaluation.current_score == 4
    assert FakeRuleRunner.calls == []


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


def test_score_geometry_raises_input_error_when_big_image_missing():
    """验证几何评分节点发现大图缺失时会快速失败。"""
    config = Rule8Config(groove_width_center=1, groove_width_side=1)

    with pytest.raises(InputDataError, match="big_image is required"):
        score_geometry(None, [config])


def test_score_geometry_raises_input_error_when_evaluation_missing():
    """验证几何评分节点发现大图 evaluation 缺失时会快速失败。"""
    config = Rule8Config(groove_width_center=1, groove_width_side=1)
    big_image = make_big_image()

    with pytest.raises(InputDataError, match="big_image.evaluation is required"):
        score_geometry(big_image, [config])


def test_score_geometry_raises_input_error_when_rule_evaluation_missing():
    """验证几何评分节点发现目标 RuleEvaluation 缺失时会快速失败。"""
    config = Rule8Config(groove_width_center=1, groove_width_side=1)
    big_image = make_big_image()
    big_image.evaluation = ImageEvaluation(rules=[])

    with pytest.raises(InputDataError, match="missing rule evaluation for rule8"):
        score_geometry(big_image, [config])
