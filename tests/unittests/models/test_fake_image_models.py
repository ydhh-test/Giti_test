import pytest
from pydantic import ValidationError

from src.models.fake_image_models import (
    FakeBigImage,
    FakeBigImageBiz,
    FakeImageMeta,
    FakeSmallImage,
    FakeSmallImageBiz,
)
from src.models.fake_result_models import FakeEvaluation, FakeLineage, FakeScoreResult


class TestFakeImageMeta:
    """FakeImageMeta 单元测试。"""

    def test_valid_meta(self):
        meta = FakeImageMeta(width=512, height=512, channel=3)
        expected = {
            "width": 512,
            "height": 512,
            "channel": 3,
        }
        assert meta.model_dump() == expected

    def test_invalid_width_zero(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeImageMeta(width=0, height=512, channel=3)
        assert "FakeImageMeta.width: must be positive, got 0" in str(exc_info.value)

    def test_invalid_width_negative(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeImageMeta(width=-1, height=512, channel=3)
        assert "FakeImageMeta.width: must be positive, got -1" in str(exc_info.value)

    def test_invalid_height_zero(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeImageMeta(width=512, height=0, channel=3)
        assert "FakeImageMeta.height: must be positive, got 0" in str(exc_info.value)

    def test_invalid_channel_zero(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeImageMeta(width=512, height=512, channel=0)
        assert "FakeImageMeta.channel: must be positive, got 0" in str(exc_info.value)


class TestFakeSmallImageBiz:
    """FakeSmallImageBiz 单元测试。"""

    def test_valid_biz(self):
        biz = FakeSmallImageBiz(image_id="img-001")
        expected = {
            "image_id": "img-001",
            "position": None,
            "camera_id": None,
        }
        assert biz.model_dump() == expected

    def test_valid_biz_with_optional(self):
        biz = FakeSmallImageBiz(
            image_id="img-001",
            position="left",
            camera_id="cam-01",
        )
        expected = {
            "image_id": "img-001",
            "position": "left",
            "camera_id": "cam-01",
        }
        assert biz.model_dump() == expected

    def test_invalid_image_id_empty(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeSmallImageBiz(image_id="")
        assert "FakeSmallImageBiz.image_id: must not be empty, got ''" in str(exc_info.value)


class TestFakeSmallImage:
    """FakeSmallImage 单元测试。"""

    def test_valid_small_image(self):
        img = FakeSmallImage(
            image_base64="data:image/png;base64,AAA...",
            meta=FakeImageMeta(width=512, height=512, channel=3),
            biz=FakeSmallImageBiz(image_id="img-001"),
            evaluation=FakeEvaluation(features=[]),
        )
        expected = {
            "image_base64": "data:image/png;base64,AAA...",
            "meta": {"width": 512, "height": 512, "channel": 3},
            "biz": {"image_id": "img-001", "position": None, "camera_id": None},
            "evaluation": {"features": []},
        }
        assert img.model_dump() == expected

    def test_invalid_image_base64_empty(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeSmallImage(
                image_base64="",
                meta=FakeImageMeta(width=512, height=512, channel=3),
                biz=FakeSmallImageBiz(image_id="img-001"),
                evaluation=FakeEvaluation(features=[]),
            )
        assert "FakeBaseImage.image_base64: must not be empty, got ''" in str(exc_info.value)


class TestFakeBigImageBiz:
    def test_invalid_image_id_empty(self):
        with pytest.raises(ValidationError) as exc_info:
            FakeBigImageBiz(image_id="", scheme_rank=1, status="generated")

        assert "FakeBigImageBiz.image_id: must not be empty, got ''" in str(exc_info.value)


class TestFakeBigImage:
    def test_valid_big_image(self):
        big_image = FakeBigImage(
            image_base64="data:image/png;base64,CCC...",
            meta=FakeImageMeta(width=1024, height=512, channel=3),
            biz=FakeBigImageBiz(image_id="big-001", scheme_rank=1, status="generated"),
            evaluation=FakeEvaluation(features=[]),
            scores=[
                FakeScoreResult(
                    rule_name="rule8",
                    description="横沟数量检测",
                    score_value=4.0,
                    score_max=4.0,
                    reason="横沟数量满足要求",
                )
            ],
            lineage=FakeLineage(
                source_image_ids=["img-001", "img-002"],
                scheme_rank=1,
                summary="由 2 张小图按第 1 名方案生成大图",
            ),
        )
        expected = {
            "biz": {
                "image_id": "big-001",
                "scheme_rank": 1,
                "status": "generated",
            },
            "lineage": {
                "source_image_ids": ["img-001", "img-002"],
                "scheme_rank": 1,
                "summary": "由 2 张小图按第 1 名方案生成大图",
            },
        }
        actual = {
            "biz": big_image.biz.model_dump(),
            "lineage": big_image.lineage.model_dump(),
        }
        assert actual == expected
