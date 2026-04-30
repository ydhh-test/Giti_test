import pytest
from pydantic import ValidationError

from src.models.fake_result_models import (
    FakeEvaluation,
    FakeFeatureResult,
    FakeLineage,
    FakeScoreResult,
)


class TestFakeFeatureResult:
    def test_valid_feature_result(self):
        feature = FakeFeatureResult(
            rule_name="rule6-1",
            feature_name="pattern_continuity",
            feature_value="good",
            description="图案连续性",
        )

        assert feature.model_dump() == {
            "rule_name": "rule6-1",
            "feature_name": "pattern_continuity",
            "feature_value": "good",
            "description": "图案连续性",
        }

    def test_invalid_rule_name(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeFeatureResult(
                rule_name="wrong",
                feature_name="pattern_continuity",
                feature_value="good",
                description="图案连续性",
            )

        assert "FakeFeatureResult.rule_name: must be 'rule6-1' or 'rule8', got 'wrong'" in str(exc_info.value)


class TestFakeEvaluation:
    def test_valid_empty_features(self):
        evaluation = FakeEvaluation(features=[])

        assert evaluation.model_dump() == {"features": []}

    def test_valid_features(self):
        evaluation = FakeEvaluation(
            features=[
                FakeFeatureResult(
                    rule_name="rule8",
                    feature_name="groove_count",
                    feature_value="1",
                    description="横沟数量",
                )
            ]
        )

        assert evaluation.model_dump() == {
            "features": [
                {
                    "rule_name": "rule8",
                    "feature_name": "groove_count",
                    "feature_value": "1",
                    "description": "横沟数量",
                }
            ]
        }


class TestFakeScoreResult:
    def test_valid_score_result(self):
        score = FakeScoreResult(
            rule_name="rule8",
            description="横沟数量检测",
            score_value=4.0,
            score_max=4.0,
            reason="横沟数量满足要求",
        )

        assert score.model_dump() == {
            "rule_name": "rule8",
            "description": "横沟数量检测",
            "score_value": 4.0,
            "score_max": 4.0,
            "reason": "横沟数量满足要求",
        }

    def test_invalid_rule_name(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeScoreResult(
                rule_name="wrong",
                description="横沟数量检测",
                score_value=4.0,
                score_max=4.0,
                reason="横沟数量满足要求",
            )

        assert "FakeScoreResult.rule_name: must be 'rule6-1' or 'rule8', got 'wrong'" in str(exc_info.value)

    def test_invalid_score_value_gt_score_max(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeScoreResult(
                rule_name="rule8",
                description="横沟数量检测",
                score_value=5.0,
                score_max=4.0,
                reason="横沟数量不满足要求",
            )

        assert "FakeScoreResult.score_value: must be less than or equal to score_max, got 5.0" in str(exc_info.value)


class TestFakeLineage:
    def test_valid_lineage(self):
        lineage = FakeLineage(
            source_image_ids=["small-001", "small-002"],
            scheme_rank=1,
            summary="由 2 张小图按第 1 名方案生成大图",
        )

        assert lineage.model_dump() == {
            "source_image_ids": ["small-001", "small-002"],
            "scheme_rank": 1,
            "summary": "由 2 张小图按第 1 名方案生成大图",
        }
