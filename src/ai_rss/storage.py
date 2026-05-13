from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .models import Item

from .timeutils import parse_datetime


class Storage:
    def __init__(self, path: Path) -> None:
        self.path = path

    def init(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists items (
                    id integer primary key autoincrement,
                    title text not null,
                    source_name text not null,
                    source_type text not null,
                    source_priority text not null,
                    url text not null,
                    canonical_url text not null unique,
                    published_at text,
                    collected_at text not null,
                    summary text not null default '',
                    tags_json text not null default '[]',
                    score integer not null default 0
                )
                """
            )

    def upsert_item(self, item: Item) -> None:
        collected_at = datetime.now().astimezone().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                insert into items (
                    title, source_name, source_type, source_priority, url, canonical_url,
                    published_at, collected_at, summary, tags_json, score
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(canonical_url) do update set
                    title = excluded.title,
                    source_name = excluded.source_name,
                    source_type = excluded.source_type,
                    source_priority = excluded.source_priority,
                    url = excluded.url,
                    published_at = coalesce(excluded.published_at, items.published_at),
                    summary = excluded.summary,
                    tags_json = excluded.tags_json
                """,
                (
                    item.title,
                    item.source_name,
                    item.source_type,
                    item.source_priority,
                    item.url,
                    item.canonical_url,
                    item.published_at,
                    collected_at,
                    item.summary,
                    json.dumps(item.tags, ensure_ascii=False),
                    item.score,
                ),
            )

    def list_items_between(self, start: datetime, end: datetime) -> list[Item]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                select title, source_name, source_type, source_priority, url, canonical_url,
                       published_at, collected_at, summary, tags_json, score
                from items
                order by coalesce(published_at, collected_at) desc, id desc
                """
            ).fetchall()
        items = []
        for row in rows:
            timestamp = parse_datetime(row["published_at"] or row["collected_at"])
            timestamp = timestamp.astimezone(start.tzinfo)
            if not (start <= timestamp < end):
                continue
            items.append(
                Item(
                    title=row["title"],
                    source_name=row["source_name"],
                    source_type=row["source_type"],
                    source_priority=row["source_priority"],
                    url=row["url"],
                    canonical_url=row["canonical_url"],
                    published_at=row["published_at"],
                    summary=row["summary"],
                    tags=json.loads(row["tags_json"]),
                    score=int(row["score"]),
                )
            )
        return items

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn
