import json
from pathlib import Path

from ai_rss.brief import create_brief_from_candidates
from ai_rss.llm import LLMEnhancement
from ai_rss.models import Item
from ai_rss.scoring import score_items


def make_item(
    title: str,
    *,
    source_name: str = "Example Blog",
    source_type: str = "rss",
    source_priority: str = "P1",
    summary: str = "",
    tags: list[str] | None = None,
) -> Item:
    return Item(
        title=title,
        source_name=source_name,
        source_type=source_type,
        source_priority=source_priority,
        url=f"https://example.com/{title.lower().replace(' ', '-')}",
        canonical_url=f"https://example.com/{title.lower().replace(' ', '-')}",
        published_at="2026-05-13T08:00:00+00:00",
        summary=summary,
        tags=tags or [],
    )


def test_scoring_prioritizes_ai_coding_and_penalizes_low_credibility() -> None:
    scored = score_items(
        [
            make_item(
                "Copilot coding agent can repair failing CI and open PRs",
                source_name="GitHub Blog",
                source_priority="P0",
                summary="Official release improves repo understanding, test generation, and automatic pull requests.",
            ),
            make_item(
                "Unverified rumor says a mystery model may launch",
                source_name="Random Aggregator",
                source_priority="P2",
                summary="Rumor with no source, benchmark, paper, repo, demo, or official confirmation.",
            ),
        ]
    )

    assert scored[0].title.startswith("Copilot coding agent")
    assert scored[0].score >= 80
    assert "ai-coding" in scored[0].tags
    assert "software-delivery" in scored[0].tags
    assert scored[1].score < 40
    assert 0 <= scored[1].score <= 100


def test_creates_review_brief_from_candidates_with_sections_and_exploration_quota(tmp_path: Path) -> None:
    candidates_dir = tmp_path / "candidates"
    candidates_dir.mkdir()
    candidate_file = candidates_dir / "2026-05-13.json"
    candidate_file.write_text(
        json.dumps(
            {
                "brief_date": "2026-05-13",
                "items": [
                    candidate(
                        "GitHub ships Copilot coding agent for pull requests",
                        "GitHub Blog",
                        "P0",
                        "Official release improves repo understanding, CI repair, tests, and automatic PRs.",
                        practical_takeaway="Use it first on repositories with reliable CI and small reviewable PR scopes.",
                    ),
                    candidate(
                        "Harness adds AI release automation for software delivery",
                        "Harness Blog",
                        "P0",
                        "Official release connects CI/CD, deployment verification, and developer productivity.",
                        practical_takeaway="Compare the workflow against existing release gates before broad rollout.",
                    ),
                    candidate(
                        "OpenAI releases new model API for tool use",
                        "OpenAI Blog",
                        "P0",
                        "Official release improves model API tool calling and benchmark performance.",
                    ),
                    candidate(
                        "Anthropic introduces agent benchmark for long-running tasks",
                        "Anthropic News",
                        "P0",
                        "Official benchmark and paper evaluate agent reliability on research tasks.",
                    ),
                    candidate(
                        "Novel inference cache project gains adoption",
                        "Independent Lab",
                        "P1",
                        "Demo, repo, and benchmark show a new technical route with potential engineering impact.",
                    ),
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    brief_path = create_brief_from_candidates(tmp_path, "2026-05-13", max_items=4)

    assert brief_path == tmp_path / "briefs" / "2026-05-13.md"
    text = brief_path.read_text(encoding="utf-8")
    assert "## Top 3 必读" in text
    assert "## AI Coding / 软件交付工程实践" in text
    assert "## 探索性高信号" in text
    assert "可落地启发：Use it first on repositories with reliable CI and small reviewable PR scopes." in text
    assert "Novel inference cache project gains adoption" in text


def test_review_brief_can_preserve_manual_edits(tmp_path: Path) -> None:
    candidates_dir = tmp_path / "candidates"
    candidates_dir.mkdir()
    (candidates_dir / "2026-05-13.json").write_text(
        json.dumps(
            {
                "brief_date": "2026-05-13",
                "items": [
                    candidate(
                        "GitHub ships Copilot coding agent",
                        "GitHub Blog",
                        "P0",
                        "Official release for coding agents and pull requests.",
                    )
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    brief_path = tmp_path / "briefs" / "2026-05-13.md"
    brief_path.parent.mkdir()
    brief_path.write_text("manual review edits\n", encoding="utf-8")

    result = create_brief_from_candidates(tmp_path, "2026-05-13", overwrite=False)

    assert result == brief_path
    assert brief_path.read_text(encoding="utf-8") == "manual review edits\n"


def test_review_brief_uses_llm_enhancements_for_selected_items(tmp_path: Path) -> None:
    candidates_dir = tmp_path / "candidates"
    candidates_dir.mkdir()
    (candidates_dir / "2026-05-13.json").write_text(
        json.dumps(
            {
                "brief_date": "2026-05-13",
                "items": [
                    candidate(
                        "GitHub ships Copilot coding agent",
                        "GitHub Blog",
                        "P0",
                        "Official release for coding agents and pull requests.",
                    )
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    class FakeLLMClient:
        def enhance(self, item: Item) -> LLMEnhancement:
            return LLMEnhancement(
                summary="LLM 摘要：GitHub 发布 coding agent。",
                key_changes="LLM 关键变化：支持从 issue 到 PR。",
                why_matters="LLM 重要性：会改变后台开发的代码审查流程。",
                practical_takeaway="LLM 启发：先在小仓库试用。",
            )

    brief_path = create_brief_from_candidates(tmp_path, "2026-05-13", llm_client=FakeLLMClient())

    text = brief_path.read_text(encoding="utf-8")
    assert "摘要：LLM 摘要：GitHub 发布 coding agent。" in text
    assert "关键变化：LLM 关键变化：支持从 issue 到 PR。" in text
    assert "为什么重要：LLM 重要性：会改变后台开发的代码审查流程。" in text
    assert "可落地启发：LLM 启发：先在小仓库试用。" in text


def test_review_brief_falls_back_when_llm_enhancement_fails(tmp_path: Path) -> None:
    candidates_dir = tmp_path / "candidates"
    candidates_dir.mkdir()
    (candidates_dir / "2026-05-13.json").write_text(
        json.dumps(
            {
                "brief_date": "2026-05-13",
                "items": [
                    candidate(
                        "Harness adds AI release automation",
                        "Harness Blog",
                        "P0",
                        "Official release connects CI/CD and deployment verification.",
                    )
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    class FailingLLMClient:
        def enhance(self, item: Item) -> LLMEnhancement:
            raise RuntimeError("provider unavailable")

    brief_path = create_brief_from_candidates(tmp_path, "2026-05-13", llm_client=FailingLLMClient())

    text = brief_path.read_text(encoding="utf-8")
    assert "Official release connects CI/CD and deployment verification." in text
    assert "provider unavailable" not in text


def candidate(
    title: str,
    source_name: str,
    source_priority: str,
    summary: str,
    *,
    tags: list[str] | None = None,
    practical_takeaway: str = "",
) -> dict[str, object]:
    url = f"https://example.com/{title.lower().replace(' ', '-')}"
    return {
        "title": title,
        "source_name": source_name,
        "source_type": "rss",
        "source_priority": source_priority,
        "url": url,
        "canonical_url": url,
        "published_at": "2026-05-13T08:00:00+00:00",
        "summary": summary,
        "tags": tags or [],
        "score": 0,
        "practical_takeaway": practical_takeaway,
    }
