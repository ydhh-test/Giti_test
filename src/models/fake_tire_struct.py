from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator

from ..common.exceptions import InputDataError
from .fake_image_models import FakeBigImage, FakeSmallImage
from .fake_rules_models import FakeRulesConfig


class FakeTireStruct(BaseModel):
    small_images: list[FakeSmallImage] = Field(default_factory=list)
    big_image: Optional[FakeBigImage] = None
    rules_config: FakeRulesConfig
    scheme_rank: int
    is_debug: bool = False
    flag: bool = False
    err_code: Optional[str] = None
    err_msg: Optional[str] = None

    model_config = {"extra": "forbid"}

    def _get_request_validation_error(self) -> InputDataError | None:
        if len(self.small_images) == 0:
            return InputDataError(
                object_name="FakeTireStruct",
                field_path="small_images",
                rule="must not be empty",
                actual_value=self.small_images,
            )
        if self.big_image is not None:
            return InputDataError(
                object_name="FakeTireStruct",
                field_path="big_image",
                rule="must be None in request",
                actual_value=self.big_image.model_dump(),
            )
        if self.scheme_rank < 1:
            return InputDataError(
                object_name="FakeTireStruct",
                field_path="scheme_rank",
                rule="must be >= 1",
                actual_value=self.scheme_rank,
            )
        if self.is_debug:
            return InputDataError(
                object_name="FakeTireStruct",
                field_path="is_debug",
                rule="must be False in current fake API",
                actual_value=self.is_debug,
            )
        if self.flag:
            return InputDataError(
                object_name="FakeTireStruct",
                field_path="flag",
                rule="must be False in request",
                actual_value=self.flag,
            )
        if self.err_code is not None:
            return InputDataError(
                object_name="FakeTireStruct",
                field_path="err_code",
                rule="must be None in request",
                actual_value=self.err_code,
            )
        if self.err_msg is not None:
            return InputDataError(
                object_name="FakeTireStruct",
                field_path="err_msg",
                rule="must be None in request",
                actual_value=self.err_msg,
            )
        return None

    def validate_request(self) -> str | None:
        error = self._get_request_validation_error()
        if error is None:
            return None
        return str(error)

    @model_validator(mode="after")
    def validate_request_on_build(self) -> "FakeTireStruct":
        error = self._get_request_validation_error()
        if error is not None:
            raise ValueError(str(error))
        return self
