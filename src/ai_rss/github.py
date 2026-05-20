from __future__ import annotations

from datetime import timezone
from typing import Any, Protocol
from urllib.parse import parse_qsl, urlsplit

import requests
from dateutil import parser as date_parser

from .config import Source
from .github_quality import passes_github_repository_quality
from .models import Item
from .normalize import canonical_url


class GitHubJsonClient(Protocol):
    def get_json(self, url: str, params: dict[str, object] | None = None) -> Any: ...


class RequestsGitHubClient:
    def get_json(self, url: str, params: dict[str, object] | None = None) -> Any:
        response = requests.get(
            url,
            params=params,
            headers={"Accept": "application/vnd.github+json"},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()


def collect_github_repositories(
    source: Source,
    *,
    client: GitHubJsonClient | None = None,
    per_page: int = 25,
) -> list[Item]:
    client = client or RequestsGitHubClient()
    url, params = _repository_search_request(source.url, per_page)
    payload = client.get_json(url, params=params)
    repositories = payload.get("items", []) if isinstance(payload, dict) else []

    items: list[Item] = []
    for repo in repositories:
        if not isinstance(repo, dict):
            continue
        item = _repository_item(source, repo)
        if item is not None:
            items.append(item)
    return items


def collect_github_releases(
    source: Source,
    *,
    client: GitHubJsonClient | None = None,
    per_page: int = 10,
) -> list[Item]:
    owner_repo = _owner_repo_from_url(source.url)
    if owner_repo is None:
        return []

    client = client or RequestsGitHubClient()
    url = f"https://api.github.com/repos/{owner_repo}/releases"
    payload = client.get_json(url, params={"per_page": per_page})
    releases = payload if isinstance(payload, list) else []

    items: list[Item] = []
    for release in releases:
        if not isinstance(release, dict):
            continue
        item = _release_item(source, owner_repo, release)
        if item is not None:
            items.append(item)
    return items


def _repository_search_request(source_url: str, per_page: int) -> tuple[str, dict[str, object]]:
    parts = urlsplit(source_url)
    params = dict(parse_qsl(parts.query, keep_blank_values=True))
    return (
        "https://api.github.com/search/repositories",
        {
            "q": params.get("q", source_url),
            "sort": params.get("sort", "stars"),
            "order": params.get("order", "desc"),
            "per_page": per_page,
        },
    )


def _owner_repo_from_url(value: str) -> str | None:
    parts = urlsplit(value)
    path = parts.path.strip("/") if parts.netloc else value.strip("/")
    bits = [bit for bit in path.split("/") if bit]
    if len(bits) < 2:
        return None
    return f"{bits[0]}/{bits[1]}"


def _repository_item(source: Source, repo: dict[str, Any]) -> Item | None:
    title = str(repo.get("full_name") or "").strip()
    url = canonical_url(str(repo.get("html_url") or ""))
    if not title or not url:
        return None

    description = str(repo.get("description") or "").strip()
    stars = int(repo.get("stargazers_count") or 0)
    if not passes_github_repository_quality(title, stars):
        return None

    summary_parts = [description] if description else []
    summary_parts.append(f"Stars: {stars}")

    topics = [str(topic) for topic in repo.get("topics") or [] if topic]
    return Item(
        title=title,
        source_name=source.name,
        source_type=source.type,
        source_priority=source.priority,
        url=url,
        canonical_url=url,
        published_at=_parse_github_date(repo.get("pushed_at") or repo.get("updated_at")),
        summary="\n".join(summary_parts),
        tags=_unique(source.tags + topics),
        score=stars,
    )


def _release_item(source: Source, owner_repo: str, release: dict[str, Any]) -> Item | None:
    name = str(release.get("name") or release.get("tag_name") or "").strip()
    url = canonical_url(str(release.get("html_url") or ""))
    if not name or not url:
        return None

    return Item(
        title=f"{owner_repo} release {name}",
        source_name=source.name,
        source_type=source.type,
        source_priority=source.priority,
        url=url,
        canonical_url=url,
        published_at=_parse_github_date(release.get("published_at") or release.get("created_at")),
        summary=str(release.get("body") or "").strip(),
        tags=_unique(source.tags + ["release"]),
    )


def _parse_github_date(value: object) -> str | None:
    if not value:
        return None
    try:
        dt = date_parser.parse(str(value))
    except (TypeError, ValueError, OverflowError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
