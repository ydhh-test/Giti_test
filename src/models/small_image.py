"""Small image model placeholders."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SmallImage(BaseModel):
    """Placeholder model for a small image and its metadata."""

    image_id: str | None = None
    image_data: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)
