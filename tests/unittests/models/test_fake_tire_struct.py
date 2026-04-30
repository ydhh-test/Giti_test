import pytest
from pydantic import ValidationError

from src.models.fake_tire_struct import FakeTireStruct


def create_valid_input() -> dict:
    return {
        "small_images": [
            {
                "image_base64": "data:image/png;base64,AAA...",
                "meta": {"width": 512, "height": 512, "channel": 3},
                "biz": {"image_id": "small-001", "position": "left", "camera_id": "cam-01"},
                "evaluation": {"features": []},
            }
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


class TestFakeTireStruct:
    def test_valid_model_validate(self):
        tire_struct = FakeTireStruct.model_validate(create_valid_input())

        assert tire_struct.model_dump() == {
            "small_images": [
                {
                    "image_base64": "data:image/png;base64,AAA...",
                    "meta": {"width": 512, "height": 512, "channel": 3},
                    "biz": {"image_id": "small-001", "position": "left", "camera_id": "cam-01"},
                    "evaluation": {"features": []},
                }
            ],
            "big_image": None,
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
            "flag": False,
            "err_code": None,
            "err_msg": None,
        }

    def test_validate_request_returns_none_when_valid(self):
        tire_struct = FakeTireStruct.model_validate(create_valid_input())

        assert tire_struct.validate_request() is None

    def test_invalid_empty_small_images(self):
        data = create_valid_input()
        data["small_images"] = []

        with pytest.raises(ValidationError) as exc_info:
            FakeTireStruct.model_validate(data)

        assert "FakeTireStruct.small_images: must not be empty, got []" in str(exc_info.value)

    def test_invalid_big_image_not_none(self):
        data = create_valid_input()
        data["big_image"] = {
            "image_base64": "data:image/png;base64,CCC...",
            "meta": {"width": 1024, "height": 512, "channel": 3},
            "biz": {"image_id": "big-001", "scheme_rank": 1, "status": "generated"},
            "evaluation": {"features": []},
            "scores": [],
            "lineage": {
                "source_image_ids": ["small-001"],
                "scheme_rank": 1,
                "summary": "由 1 张小图按第 1 名方案生成大图",
            },
        }

        with pytest.raises(ValidationError) as exc_info:
            FakeTireStruct.model_validate(data)

        assert "FakeTireStruct.big_image: must be None in request" in str(exc_info.value)

    def test_invalid_scheme_rank(self):
        data = create_valid_input()
        data["scheme_rank"] = 0

        with pytest.raises(ValidationError) as exc_info:
            FakeTireStruct.model_validate(data)

        assert "FakeTireStruct.scheme_rank: must be >= 1, got 0" in str(exc_info.value)

    def test_invalid_is_debug_true(self):
        data = create_valid_input()
        data["is_debug"] = True

        with pytest.raises(ValidationError) as exc_info:
            FakeTireStruct.model_validate(data)

        assert "FakeTireStruct.is_debug: must be False in current fake API, got True" in str(exc_info.value)

    def test_invalid_flag_true(self):
        data = create_valid_input()
        data["flag"] = True

        with pytest.raises(ValidationError) as exc_info:
            FakeTireStruct.model_validate(data)

        assert "FakeTireStruct.flag: must be False in request, got True" in str(exc_info.value)

    def test_invalid_err_code_not_none(self):
        data = create_valid_input()
        data["err_code"] = "DATA_ERROR"

        with pytest.raises(ValidationError) as exc_info:
            FakeTireStruct.model_validate(data)

        assert "FakeTireStruct.err_code: must be None in request, got 'DATA_ERROR'" in str(exc_info.value)

    def test_invalid_err_msg_not_none(self):
        data = create_valid_input()
        data["err_msg"] = "bad request"

        with pytest.raises(ValidationError) as exc_info:
            FakeTireStruct.model_validate(data)

        assert "FakeTireStruct.err_msg: must be None in request, got 'bad request'" in str(exc_info.value)

    def test_validate_request_returns_error_message_for_constructed_invalid_instance(self):
        validated = FakeTireStruct.model_validate(create_valid_input())
        tire_struct = FakeTireStruct.model_construct(
            small_images=validated.small_images,
            big_image=None,
            rules_config=validated.rules_config,
            scheme_rank=validated.scheme_rank,
            is_debug=validated.is_debug,
            flag=True,
            err_code=None,
            err_msg=None,
        )

        assert tire_struct.validate_request() == "FakeTireStruct.flag: must be False in request, got True"
