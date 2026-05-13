import json
import sqlite3
from pathlib import Path

from ai_rss.cli import main


def test_collect_generates_candidate_files_and_is_idempotent(tmp_path: Path) -> None:
    rss_file = tmp_path / "feed.xml"
    rss_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example AI Blog</title>
    <item>
      <title>New Coding Agent Release</title>
      <link>https://example.com/coding-agent</link>
      <pubDate>Wed, 13 May 2026 08:00:00 GMT</pubDate>
      <description>Agent can open pull requests and repair tests.</description>
    </item>
  </channel>
</rss>
""",
        encoding="utf-8",
    )
    config = tmp_path / "sources.yaml"
    config.write_text(
        f"""
sources:
  - name: Example AI Blog
    type: rss
    priority: P0
    url: {rss_file.as_uri()}
    tags: [ai-coding]
    enabled: true
""",
        encoding="utf-8",
    )

    args = [
        "collect",
        "--config",
        str(config),
        "--data-dir",
        str(tmp_path),
        "--now",
        "2026-05-13T18:00:00+08:00",
    ]

    assert main(args) == 0
    assert main(args) == 0

    candidates_md = tmp_path / "candidates" / "2026-05-13.md"
    candidates_json = tmp_path / "candidates" / "2026-05-13.json"
    assert candidates_md.exists()
    assert candidates_json.exists()
    assert "New Coding Agent Release" in candidates_md.read_text(encoding="utf-8")

    payload = json.loads(candidates_json.read_text(encoding="utf-8"))
    assert [item["title"] for item in payload["items"]] == ["New Coding Agent Release"]

    with sqlite3.connect(tmp_path / "app.db") as conn:
        count = conn.execute("select count(*) from items").fetchone()[0]
    assert count == 1
