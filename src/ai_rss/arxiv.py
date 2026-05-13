from __future__ import annotations

from datetime import timezone
from typing import Protocol
from xml.etree import ElementTree as ET

import requests
from dateutil import parser as date_parser

from .config import Source
from .models import Item
from .normalize import canonical_url

ATOM = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class TextClient(Protocol):
    def get_text(self, url: str) -> str: ...


class RequestsTextClient:
    def get_text(self, url: str) -> str:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response.text


def collect_arxiv_query(source: Source, *, client: TextClient | None = None) -> list[Item]:
    client = client or RequestsTextClient()
    return parse_arxiv_atom(source, client.get_text(source.url))


def parse_arxiv_atom(source: Source, text: str) -> list[Item]:
    root = ET.fromstring(text)
    items: list[Item] = []
    for entry in root.findall("atom:entry", ATOM):
        title = _text(entry, "atom:title")
        url = _alternate_link(entry) or _text(entry, "atom:id")
        if not title or not url:
            continue
        categories = _primary_categories(entry) + [
            category.attrib["term"]
            for category in entry.findall("atom:category", ATOM)
            if category.attrib.get("term")
        ]
        items.append(
            Item(
                title=_clean(title),
                source_name=source.name,
                source_type=source.type,
                source_priority=source.priority,
                url=canonical_url(url),
                canonical_url=canonical_url(url),
                published_at=_parse_date(_text(entry, "atom:published") or _text(entry, "atom:updated")),
                summary=_clean(_text(entry, "atom:summary")),
                tags=_unique(source.tags + ["paper"] + categories),
            )
        )
    return items


def _alternate_link(entry: ET.Element) -> str:
    for link in entry.findall("atom:link", ATOM):
        if link.attrib.get("rel") == "alternate" and link.attrib.get("href"):
            return link.attrib["href"]
    return ""


def _primary_categories(entry: ET.Element) -> list[str]:
    category = entry.find("arxiv:primary_category", ATOM)
    if category is None or not category.attrib.get("term"):
        return []
    return [category.attrib["term"]]


def _text(entry: ET.Element, path: str) -> str:
    found = entry.find(path, ATOM)
    return found.text if found is not None and found.text else ""


def _clean(value: str) -> str:
    return " ".join(value.split())


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


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
