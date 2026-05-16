from __future__ import annotations

import re
from datetime import timezone
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from .config import Source
from .feed import RSS_HEADERS
from .models import Item
from .normalize import canonical_url

MAX_WEB_ITEMS = 20
MIN_TITLE_LENGTH = 18
SKIP_TITLE_PREFIXES = ("image:",)
SKIP_TITLES = {
    "blog",
    "careers",
    "company",
    "contact sales",
    "developer docs",
    "developers",
    "docs",
    "engineering",
    "events",
    "foundation",
    "log in",
    "news",
    "pricing",
    "products",
    "research",
    "safety",
    "security",
    "start building",
    "try chatgpt",
    "try claude",
}


def collect_web_page(source: Source) -> list[Item]:
    response = requests.get(source.url, headers=RSS_HEADERS, timeout=8)
    response.raise_for_status()
    return parse_web_page(source, response.text)


def parse_web_page(source: Source, html: str) -> list[Item]:
    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlsplit(source.url).netloc
    seen: set[str] = set()
    items: list[Item] = []

    for anchor in soup.find_all("a", href=True):
        title = _clean_text(anchor.get_text(" ", strip=True))
        if not _looks_like_article_title(title):
            continue
        url = canonical_url(urljoin(source.url, str(anchor["href"])))
        if not url or url in seen:
            continue
        if urlsplit(url).netloc != base_domain:
            continue
        seen.add(url)
        items.append(
            Item(
                title=_strip_date_suffix(title),
                source_name=source.name,
                source_type=source.type,
                source_priority=source.priority,
                url=url,
                canonical_url=url,
                published_at=_parse_date_from_text(title),
                summary=title,
                tags=source.tags,
            )
        )
        if len(items) >= MAX_WEB_ITEMS:
            break

    return items


def _looks_like_article_title(title: str) -> bool:
    lowered = title.lower()
    if len(title) < MIN_TITLE_LENGTH:
        return False
    if lowered in SKIP_TITLES:
        return False
    return not lowered.startswith(SKIP_TITLE_PREFIXES)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _parse_date_from_text(text: str) -> str | None:
    match = re.search(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},\s+\d{4}\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    try:
        dt = date_parser.parse(match.group(0))
    except (TypeError, ValueError, OverflowError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _strip_date_suffix(title: str) -> str:
    return re.sub(
        r"\s+(?:Engineering|Research|Product|Company|Security|Safety)?\s*"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},\s+\d{4}\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
