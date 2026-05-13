from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Source:
    name: str
    type: str
    priority: str
    url: str
    tags: list[str] = field(default_factory=list)
    enabled: bool = True


def load_sources(path: Path) -> list[Source]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sources: list[Source] = []
    for raw in payload.get("sources", []):
        if not isinstance(raw, dict):
            continue
        sources.append(_source_from_dict(raw))
    return sources


def _source_from_dict(raw: dict[str, Any]) -> Source:
    return Source(
        name=str(raw["name"]),
        type=str(raw["type"]),
        priority=str(raw.get("priority", "P2")),
        url=str(raw["url"]),
        tags=list(raw.get("tags") or []),
        enabled=bool(raw.get("enabled", True)),
    )
