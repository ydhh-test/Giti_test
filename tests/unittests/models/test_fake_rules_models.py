import pytest
from pydantic import ValidationError

from src.models.fake_rules_models import (
    FakeGroovesWidthMm,
    FakeRule6_1,
    FakeRule6_1Config,
    FakeRule8,
    FakeRule8Config,
    FakeRulesConfig,
)
from src.models.fake_tire_struct import FakeTireStruct


def create_valid_rules_config_dict() -> dict:
    return {
        "rule6_1": {
            "rule_name": "rule6-1",
            "description": "图案连续性检测",
            "score": 10,
            "rule_config": {"gray_threshold_lte": 200},
        },
        "rule8": {
            "rule_name": "rule8",
            "description": "横沟数量检测",
            "score": 4,
            "rule_config": {
                "grooves_width_mm": {"center": 3.5, "side": 1.8},
                "grooves_lte": 1,
            },
        },
    }


class TestFakeRule6_1:
    def test_valid_rule6_1(self):
        rule = FakeRule6_1(
            rule_name="rule6-1",
            description="图案连续性检测",
            score=10.0,
            rule_config=FakeRule6_1Config(gray_threshold_lte=200),
        )
        expected = {
            "rule_name": "rule6-1",
            "description": "图案连续性检测",
            "score": 10.0,
            "rule_config": {"gray_threshold_lte": 200},
        }
        assert rule.model_dump() == expected

    def test_invalid_rule_name(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeRule6_1(
                rule_name="wrong",
                description="图案连续性检测",
                score=10.0,
                rule_config=FakeRule6_1Config(gray_threshold_lte=200),
            )
        assert "FakeRule6_1.rule_name: must be 'rule6-1', got 'wrong'" in str(exc_info.value)

    def test_invalid_score_negative(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeRule6_1(
                rule_name="rule6-1",
                description="图案连续性检测",
                score=-1.0,
                rule_config=FakeRule6_1Config(gray_threshold_lte=200),
            )
        assert "FakeRuleConfigBase.score: must be non-negative, got -1.0" in str(exc_info.value)


class TestFakeRule8:
    def test_valid_rule8(self):
        rule = FakeRule8(
            rule_name="rule8",
            description="横沟数量检测",
            score=4.0,
            rule_config=FakeRule8Config(
                grooves_width_mm=FakeGroovesWidthMm(center=3.5, side=1.8),
                grooves_lte=1,
            ),
        )
        expected = {
            "rule_name": "rule8",
            "description": "横沟数量检测",
            "score": 4.0,
            "rule_config": {
                "grooves_width_mm": {"center": 3.5, "side": 1.8},
                "grooves_lte": 1,
            },
        }
        assert rule.model_dump() == expected

    def test_invalid_rule_name(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeRule8(
                rule_name="wrong",
                description="横沟数量检测",
                score=4.0,
                rule_config=FakeRule8Config(
                    grooves_width_mm=FakeGroovesWidthMm(center=3.5, side=1.8),
                    grooves_lte=1,
                ),
            )
        assert "FakeRule8.rule_name: must be 'rule8', got 'wrong'" in str(exc_info.value)

    def test_invalid_grooves_lte_negative(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeRule8Config(
                grooves_width_mm=FakeGroovesWidthMm(center=3.5, side=1.8),
                grooves_lte=-1,
            )
        assert "FakeRule8Config.grooves_lte: must be non-negative, got -1" in str(exc_info.value)

    def test_invalid_grooves_width_not_positive(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeGroovesWidthMm(center=0, side=1.8)
        assert "FakeGroovesWidthMm.center: must be positive, got 0.0" in str(exc_info.value)


class TestFakeRulesConfig:
    def test_valid_rules_config(self):
        rules_config = FakeRulesConfig.model_validate(create_valid_rules_config_dict())

        assert rules_config.model_dump() == {
            "rule6_1": {
                "rule_name": "rule6-1",
                "description": "图案连续性检测",
                "score": 10.0,
                "rule_config": {"gray_threshold_lte": 200},
            },
            "rule8": {
                "rule_name": "rule8",
                "description": "横沟数量检测",
                "score": 4.0,
                "rule_config": {
                    "grooves_width_mm": {"center": 3.5, "side": 1.8},
                    "grooves_lte": 1,
                },
            },
        }

    def test_fake_tire_struct_validate_request_returns_none_when_valid(self):
        validated_tire_struct = FakeTireStruct.model_validate(
            {
                "small_images": [
                    {
                        "image_base64": "data:image/png;base64,AAA...",
                        "meta": {"width": 512, "height": 512, "channel": 3},
                        "biz": {"image_id": "small-001", "position": "left", "camera_id": "cam-01"},
                        "evaluation": {"features": []},
                    }
                ],
                "big_image": None,
                "rules_config": create_valid_rules_config_dict(),
                "scheme_rank": 1,
                "is_debug": False,
                "flag": False,
                "err_code": None,
                "err_msg": None,
            }
        )

        tire_struct = FakeTireStruct.model_construct(
            small_images=validated_tire_struct.small_images,
            big_image=None,
            rules_config=validated_tire_struct.rules_config,
            scheme_rank=1,
            is_debug=False,
            flag=False,
            err_code=None,
            err_msg=None,
        )

        assert tire_struct.validate_request() is None
