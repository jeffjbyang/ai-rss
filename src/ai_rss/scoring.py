from __future__ import annotations

from dataclasses import replace

from .models import Item

SOURCE_AUTHORITY = {
    "P0": 25,
    "P1": 18,
    "P2": 10,
}

AI_CODING_KEYWORDS = {
    "agentic coding",
    "ai coding",
    "aider",
    "automatic pr",
    "ci failure",
    "claude code",
    "cline",
    "code agent",
    "code review",
    "coderabbit",
    "coding agent",
    "codex",
    "continue",
    "copilot",
    "devin",
    "factory",
    "openhands",
    "pull request",
    "repo understanding",
    "roo code",
    "sourcegraph",
    "swe-agent",
    "test generation",
    "windsurf",
}

SOFTWARE_DELIVERY_KEYWORDS = {
    "architecture",
    "ci/cd",
    "deployment",
    "developer productivity",
    "devops",
    "engineering",
    "harness",
    "incident",
    "latency",
    "observability",
    "postmortem",
    "production",
    "reliability",
    "release automation",
    "scaling",
    "software delivery",
    "test automation",
}

ENGINEERING_PRACTICE_KEYWORDS = {
    "architecture",
    "case study",
    "context engineering",
    "deployment",
    "engineering",
    "harness",
    "incident",
    "infrastructure",
    "latency",
    "postmortem",
    "production",
    "reliability",
    "sandbox",
    "scaling",
    "tool use",
}

TECHNICAL_IMPACT_KEYWORDS = {
    "agent",
    "api",
    "benchmark",
    "coding",
    "deployment",
    "fine-tuning",
    "inference",
    "model",
    "open source",
    "platform",
    "release",
    "repo",
    "research",
    "tool",
}

NOVELTY_KEYWORDS = {
    "announces",
    "first",
    "improves",
    "introduces",
    "launch",
    "new",
    "preview",
    "release",
    "ships",
    "unveils",
}

PROPAGATION_KEYWORDS = {
    "adopts",
    "benchmark",
    "case study",
    "demo",
    "github",
    "hn",
    "paper",
    "repo",
    "trend",
}

CREDIBILITY_RISK_KEYWORDS = {
    "alleged",
    "leak",
    "may",
    "mystery",
    "no source",
    "rumor",
    "unconfirmed",
    "unverified",
}

VERIFYING_KEYWORDS = {
    "benchmark",
    "case study",
    "demo",
    "docs",
    "official",
    "paper",
    "repo",
}

EXPLORATION_GROWTH_KEYWORDS = {
    "adoption",
    "gains",
    "growth",
    "stars",
    "trend",
}

EXPLORATION_ROUTE_KEYWORDS = {
    "new architecture",
    "new technical route",
    "novel",
    "route",
}

EXPLORATION_ENGINEERING_KEYWORDS = {
    "deployment",
    "developer",
    "engineering",
    "inference",
    "tool",
}


def score_items(items: list[Item]) -> list[Item]:
    """Return scored candidates sorted by descending editorial priority."""
    return sorted((_score_item(item) for item in items), key=_sort_key, reverse=True)


def _score_item(item: Item) -> Item:
    text = _search_text(item)
    tags = _tags_for(item, text)

    raw_score = (
        _source_authority(item)
        + _technical_impact(text)
        + _novelty(text)
        + _propagation(text)
        + _theme_match(text, tags)
        - _credibility_penalty(text)
    )
    score = min(100, max(0, raw_score))
    return replace(item, score=score, tags=tags)


def _sort_key(item: Item) -> tuple[int, int, int]:
    ai_preference = int("ai-coding" in item.tags or "software-delivery" in item.tags)
    source_preference = SOURCE_AUTHORITY.get(item.source_priority.upper(), 0)
    return (item.score, ai_preference, source_preference)


def _source_authority(item: Item) -> int:
    return SOURCE_AUTHORITY.get(item.source_priority.upper(), 8)


def _technical_impact(text: str) -> int:
    matches = _match_count(text, TECHNICAL_IMPACT_KEYWORDS)
    return min(25, 10 + matches * 4)


def _novelty(text: str) -> int:
    matches = _match_count(text, NOVELTY_KEYWORDS)
    return min(15, matches * 5)


def _propagation(text: str) -> int:
    matches = _match_count(text, PROPAGATION_KEYWORDS)
    return min(15, matches * 4)


def _theme_match(text: str, tags: list[str]) -> int:
    if "ai-coding" in tags and "software-delivery" in tags:
        return 15
    if "ai-coding" in tags or "software-delivery" in tags:
        return 12
    if "ai" in text or "llm" in text or "model" in text:
        return 7
    return 0


def _credibility_penalty(text: str) -> int:
    risk = _match_count(text, CREDIBILITY_RISK_KEYWORDS)
    if risk == 0:
        return 0
    has_verification = any(keyword in text for keyword in VERIFYING_KEYWORDS)
    penalty = risk * 8
    if not has_verification:
        penalty += 6
    return min(20, penalty)


def _tags_for(item: Item, text: str) -> list[str]:
    tags = list(dict.fromkeys(item.tags))
    if _match_count(text, AI_CODING_KEYWORDS) and "ai-coding" not in tags:
        tags.append("ai-coding")
    if _match_count(text, SOFTWARE_DELIVERY_KEYWORDS) and "software-delivery" not in tags:
        tags.append("software-delivery")
    if _match_count(text, ENGINEERING_PRACTICE_KEYWORDS) and "engineering-practice" not in tags:
        tags.append("engineering-practice")
    if "ci" in text and "repair" in text and "software-delivery" not in tags:
        tags.append("software-delivery")
    if _is_exploratory_signal(text, tags) and "exploratory" not in tags:
        tags.append("exploratory")
    return tags


def _is_exploratory_signal(text: str, tags: list[str]) -> bool:
    if "ai-coding" in tags or "software-delivery" in tags:
        return False
    conditions = [
        _match_count(text, EXPLORATION_GROWTH_KEYWORDS) > 0,
        _match_count(text, EXPLORATION_ROUTE_KEYWORDS) > 0,
        _match_count(text, EXPLORATION_ENGINEERING_KEYWORDS) > 0,
        _match_count(text, VERIFYING_KEYWORDS) > 0,
    ]
    return sum(conditions) >= 2


def _match_count(text: str, keywords: set[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _search_text(item: Item) -> str:
    return " ".join([item.title, item.source_name, item.source_type, item.summary, *item.tags]).lower()
