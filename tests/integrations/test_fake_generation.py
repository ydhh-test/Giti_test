import pytest
from pydantic import ValidationError

from src.api import fake_generation
from src.api.fake_generation import generate_big_image_with_evaluation
from src.common.exceptions import InputTypeError
from src.models.fake_tire_struct import FakeTireStruct


def create_valid_input() -> dict:
    return {
        "small_images": [
            {
                "image_base64": "data:image/png;base64,AAA...",
                "meta": {"width": 512, "height": 512, "channel": 3},
                "biz": {"image_id": "small-001", "position": "left", "camera_id": "cam-01"},
                "evaluation": {"features": []},
            },
            {
                "image_base64": "data:image/png;base64,BBB...",
                "meta": {"width": 512, "height": 512, "channel": 3},
                "biz": {"image_id": "small-002", "position": "right", "camera_id": "cam-01"},
                "evaluation": {"features": []},
            },
        ],
        "big_image": None,
        "rules_config": {
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
        },
        "scheme_rank": 1,
        "is_debug": False,
        "flag": False,
        "err_code": None,
        "err_msg": None,
    }


def expected_success_output() -> dict:
    return {
        "small_images": [
            {
                "image_base64": "data:image/png;base64,AAA...",
                "meta": {"width": 512, "height": 512, "channel": 3},
                "biz": {"image_id": "small-001", "position": "left", "camera_id": "cam-01"},
                "evaluation": {"features": []},
            },
            {
                "image_base64": "data:image/png;base64,BBB...",
                "meta": {"width": 512, "height": 512, "channel": 3},
                "biz": {"image_id": "small-002", "position": "right", "camera_id": "cam-01"},
                "evaluation": {"features": []},
            },
        ],
        "big_image": {
            "image_base64": "data:image/png;base64,FAKE_BIG_IMAGE_PLACEHOLDER",
            "meta": {"width": 1024, "height": 512, "channel": 3},
            "biz": {"image_id": "big-001", "scheme_rank": 1, "status": "generated"},
            "evaluation": {
                "features": [
                    {
                        "rule_name": "rule6-1",
                        "feature_name": "pattern_continuity",
                        "feature_value": "good",
                        "description": "图案连续性",
                    },
                    {
                        "rule_name": "rule8",
                        "feature_name": "groove_count",
                        "feature_value": "1",
                        "description": "横沟数量",
                    },
                ]
            },
            "scores": [
                {
                    "rule_name": "rule6-1",
                    "description": "图案连续性检测",
                    "score_value": 8.0,
                    "score_max": 10.0,
                    "reason": "连续性基本满足要求",
                },
                {
                    "rule_name": "rule8",
                    "description": "横沟数量检测",
                    "score_value": 4.0,
                    "score_max": 4.0,
                    "reason": "横沟数量满足要求",
                },
            ],
            "lineage": {
                "source_image_ids": ["small-001", "small-002"],
                "scheme_rank": 1,
                "summary": "由 2 张小图按第 1 名方案生成大图",
            },
        },
        "rules_config": {
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
        },
        "scheme_rank": 1,
        "is_debug": False,
        "flag": True,
        "err_code": None,
        "err_msg": None,
    }


def expected_error_output(err_code: str, err_msg: str) -> dict:
    data = create_valid_input()
    data["flag"] = False
    data["err_code"] = err_code
    data["err_msg"] = err_msg
    return data


class TestFakeGenerationAPI:
    def test_success_response(self):
        data = create_valid_input()
        tire_struct = FakeTireStruct.model_validate(data)

        result = generate_big_image_with_evaluation(tire_struct)

        assert result.model_dump() == expected_success_output()

    def test_type_error_when_input_is_not_fake_tire_struct(self):
        with pytest.raises(InputTypeError) as exc_info:
            generate_big_image_with_evaluation(create_valid_input())
        assert str(exc_info.value) == (
            "generate_big_image_with_evaluation: argument 'tire_struct' expects FakeTireStruct, got dict"
        )

    def test_model_validate_fails_for_empty_small_images(self):
        data = create_valid_input()
        data["small_images"] = []

        with pytest.raises(ValidationError) as exc_info:
            FakeTireStruct.model_validate(data)

        assert "FakeTireStruct.small_images: must not be empty, got []" in str(exc_info.value)

    def test_error_response_when_explicit_validation_fails(self):
        validated_tire_struct = FakeTireStruct.model_validate(create_valid_input())
        tire_struct = FakeTireStruct.model_construct(
            small_images=validated_tire_struct.small_images,
            big_image=None,
            rules_config=validated_tire_struct.rules_config,
            scheme_rank=validated_tire_struct.scheme_rank,
            is_debug=validated_tire_struct.is_debug,
            flag=True,
            err_code=None,
            err_msg=None,
        )

        result = generate_big_image_with_evaluation(tire_struct)

        assert result.model_dump() == expected_error_output(
            "DATA_ERROR",
            "FakeTireStruct.flag: must be False in request, got True",
        )

    def test_runtime_error_is_mapped_to_runtime_error_response(self, monkeypatch: pytest.MonkeyPatch):
        data = create_valid_input()
        tire_struct = FakeTireStruct.model_validate(data)

        def mock_create_success_response(_: FakeTireStruct) -> FakeTireStruct:
            raise AttributeError("mocked failure")

        monkeypatch.setattr(fake_generation, "create_success_response", mock_create_success_response)

        result = generate_big_image_with_evaluation(tire_struct)

        assert result.model_dump() == expected_error_output(
            "RUNTIME_ERROR",
            "create_success_response: failed to build fake big image: mocked failure",
        )
