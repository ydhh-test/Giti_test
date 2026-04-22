"""Top-level business aggregate model placeholders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .big_image import BigImage
from .rules_config import RulesConfig
from .small_image import SmallImage


@dataclass
class TireStruct:
    """Aggregate placeholder for tire processing data."""

    small_images: list[SmallImage] = field(default_factory=list)
    big_image: BigImage | None = None
    rules_config: RulesConfig | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
