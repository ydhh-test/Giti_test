"""Top-level business aggregate model placeholders."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .big_image import BigImage
from .rules_config import RulesConfig
from .small_image import SmallImage


class TireStruct(BaseModel):
    """Aggregate placeholder for tire processing data."""

    small_images: list[SmallImage] = Field(default_factory=list)
    big_image: BigImage | None = None
    rules_config: RulesConfig | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
