from __future__ import annotations

from datetime import timezone

import feedparser
from dateutil import parser as date_parser

from .config import Source
from .models import Item
from .normalize import canonical_url


def collect_feed(source: Source) -> list[Item]:
    parsed = feedparser.parse(source.url)
    items: list[Item] = []
    for entry in parsed.entries:
        url = canonical_url(str(entry.get("link", "")))
        if not url:
            continue
        published = _parse_date(entry.get("published") or entry.get("updated"))
        items.append(
            Item(
                title=str(entry.get("title", "")).strip(),
                source_name=source.name,
                source_type=source.type,
                source_priority=source.priority,
                url=url,
                canonical_url=url,
                published_at=published,
                summary=str(entry.get("summary", "")).strip(),
                tags=source.tags,
            )
        )
    return items


def _parse_date(value: object) -> str | None:
    if not value:
        return None
    try:
        dt = date_parser.parse(str(value))
    except (TypeError, ValueError, OverflowError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
