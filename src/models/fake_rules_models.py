from __future__ import annotations

from pydantic import BaseModel, ValidationInfo, field_validator, model_validator

from ..common.exceptions import InputDataError


class FakeGroovesWidthMm(BaseModel):
    center: float
    side: float

    model_config = {"extra": "forbid"}

    @field_validator("center", "side")
    @classmethod
    def validate_positive(cls, v: float, info: ValidationInfo) -> float:
        if v <= 0:
            error = InputDataError(
                object_name="FakeGroovesWidthMm",
                field_path=info.field_name,
                rule="must be positive",
                actual_value=v,
            )
            raise ValueError(str(error))
        return v


class FakeRule6_1Config(BaseModel):
    gray_threshold_lte: int

    model_config = {"extra": "forbid"}


class FakeRule8Config(BaseModel):
    grooves_width_mm: FakeGroovesWidthMm
    grooves_lte: int

    model_config = {"extra": "forbid"}

    @field_validator("grooves_lte")
    @classmethod
    def validate_grooves_lte(cls, v: int) -> int:
        if v < 0:
            error = InputDataError(
                object_name="FakeRule8Config",
                field_path="grooves_lte",
                rule="must be non-negative",
                actual_value=v,
            )
            raise ValueError(str(error))
        return v


class FakeRuleConfigBase(BaseModel):
    """规则配置基类，定义公共字段。"""

    rule_name: str
    description: str
    score: float

    model_config = {"extra": "forbid"}

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        if v < 0:
            error = InputDataError(
                object_name="FakeRuleConfigBase",
                field_path="score",
                rule="must be non-negative",
                actual_value=v,
            )
            raise ValueError(str(error))
        return v


class FakeRule6_1(FakeRuleConfigBase):
    """rule6-1 规则对象，继承 FakeRuleConfigBase。"""

    rule_config: FakeRule6_1Config

    @model_validator(mode="after")
    def validate_rule_name(self) -> "FakeRule6_1":
        if self.rule_name != "rule6-1":
            error = InputDataError(
                object_name="FakeRule6_1",
                field_path="rule_name",
                rule="must be 'rule6-1'",
                actual_value=self.rule_name,
            )
            raise ValueError(str(error))
        return self


class FakeRule8(FakeRuleConfigBase):
    """rule8 规则对象，继承 FakeRuleConfigBase。"""

    rule_config: FakeRule8Config

    @model_validator(mode="after")
    def validate_rule_name(self) -> "FakeRule8":
        if self.rule_name != "rule8":
            error = InputDataError(
                object_name="FakeRule8",
                field_path="rule_name",
                rule="must be 'rule8'",
                actual_value=self.rule_name,
            )
            raise ValueError(str(error))
        return self


class FakeRulesConfig(BaseModel):
    rule6_1: FakeRule6_1
    rule8: FakeRule8

    model_config = {"extra": "forbid"}
