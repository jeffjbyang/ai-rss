from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .llm import LLMClient, LLMEnhancement, llm_client_from_env
from .models import Item
from .scoring import score_items

DEFAULT_MAX_ITEMS = 15


@dataclass(frozen=True)
class BriefEntry:
    item: Item
    practical_takeaway: str = ""
    key_changes: str = ""
    why_matters: str = ""


@dataclass(frozen=True)
class LLMStats:
    enabled: bool = False
    attempted: int = 0
    succeeded: int = 0
    failed: int = 0


@dataclass(frozen=True)
class BriefResult:
    path: Path
    llm_stats: LLMStats


def create_brief_from_candidates(
    data_dir: Path,
    brief_date: str,
    *,
    max_items: int = DEFAULT_MAX_ITEMS,
    overwrite: bool = True,
    llm_client: LLMClient | None = None,
) -> Path:
    return create_brief_result_from_candidates(
        data_dir,
        brief_date,
        max_items=max_items,
        overwrite=overwrite,
        llm_client=llm_client,
    ).path


def create_brief_result_from_candidates(
    data_dir: Path,
    brief_date: str,
    *,
    max_items: int = DEFAULT_MAX_ITEMS,
    overwrite: bool = True,
    llm_client: LLMClient | None = None,
) -> BriefResult:
    """Create a Markdown review brief from candidates/YYYY-MM-DD.json."""
    candidate_path = data_dir / "candidates" / f"{brief_date}.json"
    brief_path = data_dir / "briefs" / f"{brief_date}.md"
    if brief_path.exists() and not overwrite:
        return BriefResult(path=brief_path, llm_stats=LLMStats(enabled=False))

    payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    entries = _entries_from_payload(payload)
    selected = select_for_brief(entries, max_items=max_items)
    selected, llm_stats = enhance_entries_with_stats(
        selected,
        llm_client=llm_client if llm_client is not None else llm_client_from_env(),
    )

    brief_path.parent.mkdir(parents=True, exist_ok=True)
    brief_path.write_text(render_brief(brief_date, selected), encoding="utf-8")
    return BriefResult(path=brief_path, llm_stats=llm_stats)


def enhance_entries(entries: list[BriefEntry], *, llm_client: LLMClient | None) -> list[BriefEntry]:
    return enhance_entries_with_stats(entries, llm_client=llm_client)[0]


def enhance_entries_with_stats(
    entries: list[BriefEntry],
    *,
    llm_client: LLMClient | None,
) -> tuple[list[BriefEntry], LLMStats]:
    if llm_client is None:
        return entries, LLMStats(enabled=False)
    enhanced: list[BriefEntry] = []
    attempted = 0
    succeeded = 0
    failed = 0
    for entry in entries:
        attempted += 1
        try:
            enhancement = llm_client.enhance(entry.item)
        except Exception:  # noqa: BLE001 - LLM enhancement must never block the daily brief.
            failed += 1
            enhanced.append(entry)
            continue
        succeeded += 1
        enhanced.append(_apply_enhancement(entry, enhancement))
    return enhanced, LLMStats(enabled=True, attempted=attempted, succeeded=succeeded, failed=failed)


def render_brief(brief_date: str, entries: list[BriefEntry]) -> str:
    lines = [f"# AI 技术简报 - {brief_date}", ""]
    if not entries:
        lines.append("今日暂无高价值候选。")
        return "\n".join(lines).rstrip() + "\n"

    sections: list[tuple[str, list[BriefEntry]]] = [
        ("Top 3 必读", entries[:3]),
        ("AI Coding / 软件交付工程实践", [entry for entry in entries if _is_ai_delivery(entry.item)]),
        ("模型 / API / 平台更新", [entry for entry in entries if _matches(entry.item, {"model", "api", "platform"})]),
        ("开源项目与工具", [entry for entry in entries if _matches(entry.item, {"open source", "github", "repo", "tool"})]),
        ("论文与研究", [entry for entry in entries if _matches(entry.item, {"paper", "research", "benchmark"})]),
        ("国内动态", [entry for entry in entries if _matches(entry.item, {"deepseek", "智谱", "通义", "腾讯", "百度", "字节"})]),
        ("探索性高信号", [entry for entry in entries if _is_exploratory(entry.item)]),
    ]

    for heading, section_entries in sections:
        if not section_entries:
            continue
        lines.extend([f"## {heading}", ""])
        for entry in section_entries:
            lines.extend(_render_entry(entry))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def select_for_brief(entries: list[BriefEntry], *, max_items: int = DEFAULT_MAX_ITEMS) -> list[BriefEntry]:
    if max_items <= 0:
        return []

    ordered = sorted(entries, key=lambda entry: _sort_key(entry.item), reverse=True)
    selected = ordered[:max_items]
    exploration_quota = 2 if max_items >= 10 else 1
    selected = _ensure_exploration_quota(selected, ordered, quota=exploration_quota, max_items=max_items)
    return sorted(selected, key=lambda entry: _sort_key(entry.item), reverse=True)


def _entries_from_payload(payload: dict[str, Any]) -> list[BriefEntry]:
    raw_items = payload.get("items", [])
    items = [_item_from_raw(raw) for raw in raw_items]
    scored_by_url = {item.canonical_url: item for item in score_items(items)}

    entries = []
    for raw in raw_items:
        item = scored_by_url[str(raw.get("canonical_url") or raw.get("url") or "")]
        entries.append(
            BriefEntry(
                item=item,
                practical_takeaway=str(raw.get("practical_takeaway") or ""),
                key_changes=str(raw.get("key_changes") or ""),
                why_matters=str(raw.get("why_matters") or ""),
            )
        )
    return entries


def _item_from_raw(raw: dict[str, Any]) -> Item:
    raw_tags = raw.get("tags") or []
    tags = raw_tags if isinstance(raw_tags, list) else [str(raw_tags)]
    return Item(
        title=str(raw.get("title") or ""),
        source_name=str(raw.get("source_name") or ""),
        source_type=str(raw.get("source_type") or ""),
        source_priority=str(raw.get("source_priority") or ""),
        url=str(raw.get("url") or ""),
        canonical_url=str(raw.get("canonical_url") or raw.get("url") or ""),
        published_at=str(raw["published_at"]) if raw.get("published_at") else None,
        summary=str(raw.get("summary") or ""),
        tags=[str(tag) for tag in tags],
        score=int(raw.get("score") or 0),
    )


def _ensure_exploration_quota(
    selected: list[BriefEntry],
    ordered: list[BriefEntry],
    *,
    quota: int,
    max_items: int,
) -> list[BriefEntry]:
    selected_urls = {entry.item.canonical_url for entry in selected}
    exploration_count = sum(1 for entry in selected if _is_exploratory(entry.item))
    missing = max(0, quota - exploration_count)
    if missing == 0:
        return selected

    additions = [
        entry
        for entry in ordered
        if _is_exploratory(entry.item) and entry.item.canonical_url not in selected_urls
    ][:missing]
    if not additions:
        return selected

    result = list(selected)
    for entry in additions:
        if len(result) < max_items:
            result.append(entry)
            continue
        replace_index = _lowest_replaceable_index(result)
        if replace_index is None:
            break
        result[replace_index] = entry
    return result


def _lowest_replaceable_index(entries: list[BriefEntry]) -> int | None:
    candidates = [
        (index, entry)
        for index, entry in enumerate(entries)
        if index >= 3 and not _is_exploratory(entry.item)
    ]
    if not candidates:
        candidates = [
            (index, entry)
            for index, entry in enumerate(entries)
            if not _is_exploratory(entry.item)
        ]
    if not candidates:
        return None
    return min(candidates, key=lambda pair: _sort_key(pair[1].item))[0]


def _render_entry(entry: BriefEntry) -> list[str]:
    item = entry.item
    tag_text = ", ".join(item.tags) if item.tags else "未分类"
    key_changes = entry.key_changes or item.summary
    why_matters = entry.why_matters or _default_why_matters(item)
    summary = entry.item.summary or item.title

    lines = [
        f"### [{tag_text}] {item.title}",
        f"来源：{item.source_name}",
        f"评分：{item.score}",
        f"摘要：{summary}",
        f"关键变化：{key_changes or item.title}",
        f"为什么重要：{why_matters}",
    ]
    if _is_ai_delivery(item):
        lines.append(f"可落地启发：{entry.practical_takeaway or _default_practical_takeaway(item)}")
    lines.extend([f"链接：{item.url}", ""])
    return lines


def _default_why_matters(item: Item) -> str:
    if _is_ai_delivery(item):
        return "可能影响代码生成、代码审查、测试修复或软件交付流程的实际效率。"
    if _is_exploratory(item):
        return "具备可验证信号，值得作为非主关注方向保留观察。"
    return "可能影响开发者、模型平台或 AI 工程生态的后续实践。"


def _default_practical_takeaway(item: Item) -> str:
    if "software-delivery" in item.tags:
        return "先选择低风险流水线或内部工具做小范围验证，再评估是否进入标准交付流程。"
    return "优先在小型代码库或辅助任务中试用，观察生成质量、审查成本和回滚路径。"


def _sort_key(item: Item) -> tuple[int, int, int]:
    ai_preference = int(_is_ai_delivery(item))
    source_preference = {"P0": 3, "P1": 2, "P2": 1}.get(item.source_priority.upper(), 0)
    return (item.score, ai_preference, source_preference)


def _is_ai_delivery(item: Item) -> bool:
    return "ai-coding" in item.tags or "software-delivery" in item.tags


def _is_exploratory(item: Item) -> bool:
    return "exploratory" in item.tags


def _matches(item: Item, keywords: set[str]) -> bool:
    text = " ".join([item.title, item.summary, *item.tags]).lower()
    return any(keyword in text for keyword in keywords)


def _apply_enhancement(entry: BriefEntry, enhancement: LLMEnhancement) -> BriefEntry:
    item = entry.item
    if enhancement.summary:
        item = Item(
            title=item.title,
            source_name=item.source_name,
            source_type=item.source_type,
            source_priority=item.source_priority,
            url=item.url,
            canonical_url=item.canonical_url,
            published_at=item.published_at,
            summary=enhancement.summary,
            practical_takeaway=item.practical_takeaway,
            tags=item.tags,
            score=item.score,
        )
    return BriefEntry(
        item=item,
        practical_takeaway=enhancement.practical_takeaway or entry.practical_takeaway,
        key_changes=enhancement.key_changes or entry.key_changes,
        why_matters=enhancement.why_matters or entry.why_matters,
    )
