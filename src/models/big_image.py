"""Big image model placeholders."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BigImage(BaseModel):
    """Placeholder model for a stitched big image and related outputs."""

    image_id: str | None = None
    image_data: Any = None
    lineage: dict[str, Any] = Field(default_factory=dict)
    scores: dict[str, Any] = Field(default_factory=dict)
