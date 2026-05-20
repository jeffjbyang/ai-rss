from __future__ import annotations

import re

from .models import Item

MIN_GITHUB_REPOSITORY_STARS = 1000

TRUSTED_GITHUB_OWNERS = frozenset(
    {
        "aider-ai",
        "all-hands-ai",
        "anthropics",
        "aws",
        "cline",
        "cloudflare",
        "continuedev",
        "facebookresearch",
        "getsentry",
        "github",
        "google",
        "google-deepmind",
        "ggerganov",
        "huggingface",
        "karpathy",
        "langchain-ai",
        "microsoft",
        "modelcontextprotocol",
        "nvidia",
        "openai",
        "pytorch",
        "roocodeinc",
        "run-llama",
        "simonw",
        "sourcegraph",
        "swe-agent",
        "vercel",
    }
)


def passes_github_repository_quality(full_name: str, stars: int) -> bool:
    return stars >= MIN_GITHUB_REPOSITORY_STARS or is_trusted_github_owner(full_name)


def is_low_quality_github_repository_item(item: Item) -> bool:
    if item.source_type != "github-search":
        return False
    return not passes_github_repository_quality(item.title, _stars_for_item(item))


def is_trusted_github_owner(full_name: str) -> bool:
    owner = full_name.split("/", maxsplit=1)[0].strip().lower()
    return owner in TRUSTED_GITHUB_OWNERS


def _stars_for_item(item: Item) -> int:
    match = re.search(r"(?im)^stars:\s*(\d+)\s*$", item.summary)
    if match:
        return int(match.group(1))
    return max(0, item.score)
