"""Rules configuration model placeholders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RulesConfig:
    """Placeholder model for feature and score rule configuration."""

    feature_rules: dict[str, Any] = field(default_factory=dict)
    score_rules: dict[str, Any] = field(default_factory=dict)
