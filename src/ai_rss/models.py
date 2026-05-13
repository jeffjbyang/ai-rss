from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Item:
    title: str
    source_name: str
    source_type: str
    source_priority: str
    url: str
    canonical_url: str
    published_at: str | None
    summary: str = ""
    practical_takeaway: str = ""
    tags: list[str] = field(default_factory=list)
    score: int = 0
