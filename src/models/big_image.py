"""Big image model placeholders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BigImage:
    """Placeholder model for a stitched big image and related outputs."""

    image_id: str | None = None
    image_data: Any = None
    lineage: dict[str, Any] = field(default_factory=dict)
    scores: dict[str, Any] = field(default_factory=dict)
