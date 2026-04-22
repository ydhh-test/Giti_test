"""Small image model placeholders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SmallImage:
    """Placeholder model for a small image and its metadata."""

    image_id: str | None = None
    image_data: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
