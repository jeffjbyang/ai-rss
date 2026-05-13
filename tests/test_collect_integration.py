from pathlib import Path

from ai_rss.collect import collect_to_candidates
from ai_rss.config import Source
from ai_rss.llm import LLMEnhancement
from ai_rss.models import Item
from ai_rss.timeutils import parse_now


def test_collect_dispatches_non_rss_sources_and_creates_default_brief(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "sources.yaml"
    config.write_text(
        """
sources:
  - name: GitHub AI Repos
    type: github-search
    priority: P0
    url: https://api.github.com/search/repositories?q=agentic+coding
    tags: [github, ai-coding]
    enabled: true
  - name: arXiv AI Software Engineering
    type: arxiv
    priority: P0
    url: https://export.arxiv.org/api/query?search_query=all:agentic%20coding
    tags: [research, ai-coding]
    enabled: true
  - name: Hacker News AI Search
    type: hn-feed
    priority: P0
    url: https://hnrss.org/newest?q=agentic+coding
    tags: [community, ai-coding]
    enabled: true
""",
        encoding="utf-8",
    )
    seen_source_types: list[str] = []

    def fake_collect(source: Source) -> list[Item]:
        seen_source_types.append(source.type)
        return [
            Item(
                title=f"{source.name} coding agent update",
                source_name=source.name,
                source_type=source.type,
                source_priority=source.priority,
                url=f"https://example.com/{source.type}",
                canonical_url=f"https://example.com/{source.type}",
                published_at="2026-05-13T08:00:00+00:00",
                summary="Official demo, repo, benchmark, and CI repair signal.",
                tags=source.tags,
            )
        ]

    monkeypatch.setattr("ai_rss.collect.collect_source", fake_collect)

    collect_to_candidates(config, tmp_path, parse_now("2026-05-13T18:10:00+08:00"))

    assert seen_source_types == ["github-search", "arxiv", "hn-feed"]
    assert (tmp_path / "candidates" / "2026-05-13.json").exists()
    brief = tmp_path / "briefs" / "2026-05-13.md"
    assert brief.exists()
    assert "AI Coding / 软件交付工程实践" in brief.read_text(encoding="utf-8")


def test_collect_records_source_failures_without_blocking_daily_brief(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "sources.yaml"
    config.write_text(
        """
sources:
  - name: Broken P0
    type: rss
    priority: P0
    url: https://example.com/broken.xml
    tags: [official]
    enabled: true
  - name: Working Source
    type: rss
    priority: P1
    url: https://example.com/working.xml
    tags: [ai-coding]
    enabled: true
""",
        encoding="utf-8",
    )

    def fake_collect(source: Source) -> list[Item]:
        if source.name == "Broken P0":
            raise RuntimeError("HTTP 503")
        return [
            Item(
                title="Working coding agent update",
                source_name=source.name,
                source_type=source.type,
                source_priority=source.priority,
                url="https://example.com/working",
                canonical_url="https://example.com/working",
                published_at="2026-05-13T08:00:00+00:00",
                summary="Official repo and CI repair signal.",
                tags=source.tags,
            )
        ]

    monkeypatch.setattr("ai_rss.collect.collect_source", fake_collect)

    collect_to_candidates(config, tmp_path, parse_now("2026-05-13T18:10:00+08:00"))

    assert "Working coding agent update" in (tmp_path / "briefs" / "2026-05-13.md").read_text(encoding="utf-8")
    log = (tmp_path / "logs" / "2026-05-13.log").read_text(encoding="utf-8")
    assert "Broken P0" in log
    assert "HTTP 503" in log


def test_collect_records_storage_failures_as_source_failures(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "sources.yaml"
    config.write_text(
        """
sources:
  - name: Bad Write Source
    type: rss
    priority: P0
    url: https://example.com/bad-write.xml
    tags: [official]
    enabled: true
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "ai_rss.collect.collect_source",
        lambda source: [
            Item(
                title="Will fail during write",
                source_name=source.name,
                source_type=source.type,
                source_priority=source.priority,
                url="https://example.com/will-fail",
                canonical_url="https://example.com/will-fail",
                published_at="2026-05-13T08:00:00+00:00",
                summary="This item simulates a storage failure.",
                tags=source.tags,
            )
        ],
    )
    monkeypatch.setattr("ai_rss.collect.Storage.upsert_items", lambda self, items: (_ for _ in ()).throw(OSError("disk unavailable")))

    collect_to_candidates(config, tmp_path, parse_now("2026-05-13T18:10:00+08:00"))

    log = (tmp_path / "logs" / "2026-05-13.log").read_text(encoding="utf-8")
    assert "Bad Write Source" in log
    assert "disk unavailable" in log


def test_collect_logs_llm_enhancement_stats(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "sources.yaml"
    config.write_text(
        """
sources:
  - name: Working Source
    type: rss
    priority: P0
    url: https://example.com/working.xml
    tags: [ai-coding]
    enabled: true
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "ai_rss.collect.collect_source",
        lambda source: [
            Item(
                title="Working coding agent update",
                source_name=source.name,
                source_type=source.type,
                source_priority=source.priority,
                url="https://example.com/working",
                canonical_url="https://example.com/working",
                published_at="2026-05-13T08:00:00+00:00",
                summary="Official repo and CI repair signal.",
                tags=source.tags,
            )
        ],
    )

    class FakeLLMClient:
        def enhance(self, item: Item) -> LLMEnhancement:
            return LLMEnhancement(summary="LLM 摘要")

    monkeypatch.setattr("ai_rss.collect.llm_client_from_env", lambda: FakeLLMClient())

    collect_to_candidates(config, tmp_path, parse_now("2026-05-13T18:10:00+08:00"))

    log = (tmp_path / "logs" / "2026-05-13.log").read_text(encoding="utf-8")
    assert "llm_enabled=true" in log
    assert "llm_attempted=1" in log
    assert "llm_succeeded=1" in log
    assert "llm_failed=0" in log


def test_collect_logs_llm_failure_details(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "sources.yaml"
    config.write_text(
        """
sources:
  - name: Working Source
    type: rss
    priority: P0
    url: https://example.com/working.xml
    tags: [ai-coding]
    enabled: true
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "ai_rss.collect.collect_source",
        lambda source: [
            Item(
                title="Failing LLM candidate",
                source_name=source.name,
                source_type=source.type,
                source_priority=source.priority,
                url="https://example.com/failing-llm",
                canonical_url="https://example.com/failing-llm",
                published_at="2026-05-13T08:00:00+00:00",
                summary="Official repo and CI repair signal.",
                tags=source.tags,
            )
        ],
    )

    class FailingLLMClient:
        def enhance(self, item: Item) -> LLMEnhancement:
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr("ai_rss.collect.llm_client_from_env", lambda: FailingLLMClient())

    collect_to_candidates(config, tmp_path, parse_now("2026-05-13T18:10:00+08:00"))

    log = (tmp_path / "logs" / "2026-05-13.log").read_text(encoding="utf-8")
    assert "llm_enabled=true" in log
    assert "llm_attempted=1" in log
    assert "llm_succeeded=0" in log
    assert "llm_failed=1" in log
    assert "llm_failure title=Failing LLM candidate reason=RuntimeError: provider unavailable" in log


def test_collect_logs_llm_disabled_when_no_provider_configured(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "sources.yaml"
    config.write_text(
        """
sources:
  - name: Working Source
    type: rss
    priority: P0
    url: https://example.com/working.xml
    tags: [ai-coding]
    enabled: true
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "ai_rss.collect.collect_source",
        lambda source: [
            Item(
                title="Working coding agent update",
                source_name=source.name,
                source_type=source.type,
                source_priority=source.priority,
                url="https://example.com/working",
                canonical_url="https://example.com/working",
                published_at="2026-05-13T08:00:00+00:00",
                summary="Official repo and CI repair signal.",
                tags=source.tags,
            )
        ],
    )
    monkeypatch.setattr("ai_rss.collect.llm_client_from_env", lambda: None)

    collect_to_candidates(config, tmp_path, parse_now("2026-05-13T18:10:00+08:00"))

    log = (tmp_path / "logs" / "2026-05-13.log").read_text(encoding="utf-8")
    assert "llm_enabled=false" in log
    assert "llm_attempted=0" in log
    assert "llm_succeeded=0" in log
    assert "llm_failed=0" in log
