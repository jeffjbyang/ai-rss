from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import Item


def write_candidates(data_dir: Path, brief_date: str, items: list[Item]) -> None:
    candidates_dir = data_dir / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "brief_date": brief_date,
        "items": [asdict(item) for item in items],
    }
    (candidates_dir / f"{brief_date}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (candidates_dir / f"{brief_date}.md").write_text(_candidate_markdown(brief_date, items), encoding="utf-8")


def _candidate_markdown(brief_date: str, items: list[Item]) -> str:
    lines = [f"# AI 技术简报候选 - {brief_date}", ""]
    if not items:
        lines.append("今日暂无候选。")
    for index, item in enumerate(items, start=1):
        tag_text = ", ".join(item.tags) if item.tags else "未分类"
        lines.extend(
            [
                f"## {index}. {item.title}",
                "",
                f"- 来源：{item.source_name}",
                f"- 标签：{tag_text}",
                f"- 链接：{item.url}",
                f"- 摘要：{item.summary}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
