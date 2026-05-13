from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

BEIJING = ZoneInfo("Asia/Shanghai")


def parse_now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(tz=BEIJING)
    return parse_datetime(value)


def parse_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BEIJING)
    return dt


def brief_date_for(value: datetime) -> str:
    return value.astimezone(BEIJING).date().isoformat()


def previous_24_hour_window(now: datetime) -> tuple[datetime, datetime]:
    end = now.astimezone(BEIJING)
    return end - timedelta(hours=24), end
