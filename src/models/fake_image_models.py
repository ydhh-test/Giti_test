from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from ..common.exceptions import InputDataError
from .fake_result_models import FakeEvaluation, FakeLineage, FakeScoreResult


class FakeImageMeta(BaseModel):
    width: int
    height: int
    channel: int

    model_config = {"extra": "forbid"}

    @field_validator("width", "height", "channel")
    @classmethod
    def validate_positive(cls, v: int, info: ValidationInfo) -> int:
        if v <= 0:
            error = InputDataError(
                object_name="FakeImageMeta",
                field_path=info.field_name,
                rule="must be positive",
                actual_value=v,
            )
            raise ValueError(str(error))
        return v


class FakeSmallImageBiz(BaseModel):
    image_id: str
    position: Optional[str] = None
    camera_id: Optional[str] = None

    model_config = {"extra": "forbid"}

    @field_validator("image_id")
    @classmethod
    def validate_image_id(cls, v: str) -> str:
        if not v:
            error = InputDataError(
                object_name="FakeSmallImageBiz",
                field_path="image_id",
                rule="must not be empty",
                actual_value=v,
            )
            raise ValueError(str(error))
        return v


class FakeBigImageBiz(BaseModel):
    image_id: str
    scheme_rank: int
    status: str

    model_config = {"extra": "forbid"}

    @field_validator("image_id")
    @classmethod
    def validate_image_id(cls, v: str) -> str:
        if not v:
            error = InputDataError(
                object_name="FakeBigImageBiz",
                field_path="image_id",
                rule="must not be empty",
                actual_value=v,
            )
            raise ValueError(str(error))
        return v


class FakeBaseImage(BaseModel):
    """图像基类，定义公共字段。"""

    image_base64: str
    meta: FakeImageMeta
    evaluation: FakeEvaluation

    model_config = {"extra": "forbid"}

    @field_validator("image_base64")
    @classmethod
    def validate_image_base64(cls, v: str) -> str:
        if not v:
            error = InputDataError(
                object_name="FakeBaseImage",
                field_path="image_base64",
                rule="must not be empty",
                actual_value=v,
            )
            raise ValueError(str(error))
        return v


class FakeSmallImage(FakeBaseImage):
    """小图对象，继承 FakeBaseImage。"""

    biz: FakeSmallImageBiz


class FakeBigImage(FakeBaseImage):
    """大图对象，继承 FakeBaseImage。"""

    biz: FakeBigImageBiz
    scores: list[FakeScoreResult] = Field(default_factory=list)
    lineage: FakeLineage
