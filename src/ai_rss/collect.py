from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .arxiv import collect_arxiv_query
from .brief import LLMStats, create_brief_result_from_candidates
from .config import Source
from .config import load_sources
from .feed import collect_feed
from .github import collect_github_releases, collect_github_repositories
from .health import SourceFailure, evaluate_health, send_health_alert_to_feishu
from .hn import collect_hn_feed
from .llm import llm_client_from_env
from .render import write_candidates
from .storage import Storage
from .timeutils import brief_date_for, previous_24_hour_window


def collect_to_candidates(config_path: Path, data_dir: Path, now: datetime) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    storage = Storage(data_dir / "app.db")
    storage.init()
    source_failures: list[SourceFailure] = []

    for source in load_sources(config_path):
        if not source.enabled:
            continue
        try:
            items = collect_source(source)
            storage.upsert_items(items)
        except Exception as exc:  # noqa: BLE001 - source failures must not block the daily brief.
            source_failures.append(SourceFailure(name=source.name, priority=source.priority, reason=str(exc)))
            continue

    date = brief_date_for(now)
    start, end = previous_24_hour_window(now)
    items = storage.list_items_between(start, end)
    write_candidates(data_dir, date, items)
    brief_result = create_brief_result_from_candidates(
        data_dir,
        date,
        overwrite=True,
        llm_client=llm_client_from_env(),
    )
    report = evaluate_health(candidate_count=len(items), source_failures=source_failures)
    _write_run_log(data_dir, date, len(items), source_failures, report.reasons, brief_result.llm_stats)
    if report.needs_alert:
        send_health_alert_to_feishu(report, brief_date=date)


def collect_source(source: Source):
    if source.type == "rss":
        return collect_feed(source)
    if source.type == "github-search":
        return collect_github_repositories(source)
    if source.type == "github-releases":
        return collect_github_releases(source)
    if source.type == "arxiv":
        return collect_arxiv_query(source)
    if source.type == "hn-feed":
        return collect_hn_feed(source)
    return []


def _write_run_log(
    data_dir: Path,
    brief_date: str,
    candidate_count: int,
    source_failures: list[SourceFailure],
    health_reasons: list[str],
    llm_stats: LLMStats = LLMStats(),
) -> None:
    logs_dir = data_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"brief_date={brief_date}",
        f"candidate_count={candidate_count}",
        f"llm_enabled={str(llm_stats.enabled).lower()}",
        f"llm_attempted={llm_stats.attempted}",
        f"llm_succeeded={llm_stats.succeeded}",
        f"llm_failed={llm_stats.failed}",
    ]
    for failure in source_failures:
        lines.append(f"source_failure name={failure.name} priority={failure.priority} reason={failure.reason}")
    for reason in health_reasons:
        lines.append(f"health_reason={reason}")
    (logs_dir / f"{brief_date}.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
