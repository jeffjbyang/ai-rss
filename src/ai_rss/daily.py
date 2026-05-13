from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path

from .timeutils import BEIJING


@dataclass(frozen=True)
class DailySchedule:
    generate: datetime
    send: datetime


@dataclass(frozen=True)
class CronExamples:
    timezone: str
    generate: str
    send: str


def scheduled_times_for_brief(brief_date: str) -> DailySchedule:
    date = datetime.fromisoformat(brief_date).date()
    return DailySchedule(
        generate=datetime.combine(date, time(17, 50), tzinfo=BEIJING),
        send=datetime.combine(date, time(18, 10), tzinfo=BEIJING),
    )


def cron_examples(project_dir: Path, config_path: Path, data_dir: Path) -> CronExamples:
    prefix = f"cd {project_dir}"
    return CronExamples(
        timezone="Asia/Shanghai",
        generate=f"50 17 * * * {prefix} && ai-rss collect --config {config_path} --data-dir {data_dir}",
        send=f"10 18 * * * {prefix} && ai-rss send --data-dir {data_dir}",
    )
