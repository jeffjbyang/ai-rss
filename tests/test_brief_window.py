from pathlib import Path

from ai_rss.cli import main


def test_collect_uses_previous_24_hour_window_for_evening_brief(tmp_path: Path) -> None:
    rss_file = tmp_path / "feed.xml"
    rss_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example AI Blog</title>
    <item>
      <title>Previous Evening Inside Window</title>
      <link>https://example.com/previous-evening</link>
      <pubDate>Tue, 12 May 2026 11:00:00 GMT</pubDate>
      <description>Inside the Beijing evening brief window after 18:10.</description>
    </item>
    <item>
      <title>Same Day Inside Window</title>
      <link>https://example.com/same-day</link>
      <pubDate>Wed, 13 May 2026 09:00:00 GMT</pubDate>
      <description>Inside the Beijing evening brief window.</description>
    </item>
    <item>
      <title>Too Old</title>
      <link>https://example.com/old</link>
      <pubDate>Tue, 12 May 2026 09:00:00 GMT</pubDate>
      <description>Outside the Beijing evening brief window.</description>
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

    assert (
        main(
            [
                "collect",
                "--config",
                str(config),
                "--data-dir",
                str(tmp_path),
                "--now",
                "2026-05-13T18:10:00+08:00",
            ]
        )
        == 0
    )

    candidates = (tmp_path / "candidates" / "2026-05-13.md").read_text(encoding="utf-8")
    assert "Previous Evening Inside Window" in candidates
    assert "Same Day Inside Window" in candidates
    assert "Too Old" not in candidates
