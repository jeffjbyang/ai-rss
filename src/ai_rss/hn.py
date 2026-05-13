from __future__ import annotations

import re
from datetime import timezone
from typing import Protocol
from xml.etree import ElementTree as ET

import requests
from dateutil import parser as date_parser

from .config import Source
from .models import Item
from .normalize import canonical_url


class TextClient(Protocol):
    def get_text(self, url: str) -> str: ...


class RequestsTextClient:
    def get_text(self, url: str) -> str:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response.text


def collect_hn_feed(source: Source, *, client: TextClient | None = None) -> list[Item]:
    client = client or RequestsTextClient()
    return parse_hn_feed(source, client.get_text(source.url))


def parse_hn_feed(source: Source, text: str) -> list[Item]:
    root = ET.fromstring(text)
    items: list[Item] = []
    for entry in root.findall("./channel/item"):
        title = _child_text(entry, "title")
        url = canonical_url(_child_text(entry, "link"))
        if not title or not url:
            continue
        summary = _child_text(entry, "description")
        items.append(
            Item(
                title=title,
                source_name=source.name,
                source_type=source.type,
                source_priority=source.priority,
                url=url,
                canonical_url=url,
                published_at=_parse_date(_child_text(entry, "pubDate")),
                summary=summary,
                tags=list(dict.fromkeys(source.tags + ["hn"])),
                score=_points(summary),
            )
        )
    return items


def _child_text(entry: ET.Element, name: str) -> str:
    child = entry.find(name)
    return child.text.strip() if child is not None and child.text else ""


def _points(summary: str) -> int:
    match = re.search(r"(\d+)\s+points?", summary)
    return int(match.group(1)) if match else 0


def _parse_date(value: str) -> str | None:
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
