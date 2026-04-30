from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from ..common.exceptions import InputDataError


class FakeFeatureResult(BaseModel):
    rule_name: str
    feature_name: str
    feature_value: str
    description: str

    model_config = {"extra": "forbid"}

    @field_validator("rule_name")
    @classmethod
    def validate_rule_name(cls, v: str) -> str:
        if v not in ("rule6-1", "rule8"):
            error = InputDataError(
                object_name="FakeFeatureResult",
                field_path="rule_name",
                rule="must be 'rule6-1' or 'rule8'",
                actual_value=v,
            )
            raise ValueError(str(error))
        return v


class FakeEvaluation(BaseModel):
    features: list[FakeFeatureResult] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class FakeScoreResult(BaseModel):
    rule_name: str
    description: str
    score_value: float
    score_max: float
    reason: str

    model_config = {"extra": "forbid"}

    @field_validator("rule_name")
    @classmethod
    def validate_rule_name(cls, v: str) -> str:
        if v not in ("rule6-1", "rule8"):
            error = InputDataError(
                object_name="FakeScoreResult",
                field_path="rule_name",
                rule="must be 'rule6-1' or 'rule8'",
                actual_value=v,
            )
            raise ValueError(str(error))
        return v

    @model_validator(mode="after")
    def validate_score_range(self) -> "FakeScoreResult":
        if self.score_value > self.score_max:
            error = InputDataError(
                object_name="FakeScoreResult",
                field_path="score_value",
                rule="must be less than or equal to score_max",
                actual_value=self.score_value,
            )
            raise ValueError(str(error))
        return self


class FakeLineage(BaseModel):
    source_image_ids: list[str] = Field(default_factory=list)
    scheme_rank: int
    summary: str

    model_config = {"extra": "forbid"}
