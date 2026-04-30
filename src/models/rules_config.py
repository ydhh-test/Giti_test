"""Rules configuration model placeholders."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RulesConfig(BaseModel):
    """Placeholder model for feature and score rule configuration."""

    feature_rules: dict[str, Any] = Field(default_factory=dict)
    score_rules: dict[str, Any] = Field(default_factory=dict)
