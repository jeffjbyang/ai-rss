from __future__ import annotations

from pathlib import Path

import responses

from ai_rss.cli import main
from ai_rss.daily import cron_examples, scheduled_times_for_brief
from ai_rss.health import SourceFailure, evaluate_health, send_health_alert_to_feishu
from ai_rss.notify import send_brief_to_feishu


def test_send_brief_to_feishu_reads_daily_brief_from_env_webhook(tmp_path: Path, monkeypatch) -> None:
    brief_date = "2026-05-13"
    brief_dir = tmp_path / "briefs"
    brief_dir.mkdir()
    (brief_dir / f"{brief_date}.md").write_text("# Daily AI Brief\n\n- Codex shipped updates.\n", encoding="utf-8")
    webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/test-secret-token"
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", webhook)

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, webhook, json={"code": 0, "msg": "success"}, status=200)

        result = send_brief_to_feishu(tmp_path, brief_date)
        assert len(rsps.calls) == 1
        request = rsps.calls[0].request

    assert result.ok is True
    assert result.attempts == 1
    assert request.url == webhook
    assert b"Daily AI Brief" in request.body
    assert "test-secret-token" not in result.message


def test_send_brief_to_feishu_retries_failures_without_leaking_secret(tmp_path: Path, monkeypatch) -> None:
    brief_date = "2026-05-13"
    brief_dir = tmp_path / "briefs"
    brief_dir.mkdir()
    (brief_dir / f"{brief_date}.md").write_text("# Daily AI Brief\n", encoding="utf-8")
    webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/retry-secret-token"
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", webhook)

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, webhook, json={"code": 19001, "msg": "temporary failure"}, status=500)
        rsps.add(responses.POST, webhook, json={"code": 0, "msg": "success"}, status=200)

        result = send_brief_to_feishu(tmp_path, brief_date)
        assert len(rsps.calls) == 2

    assert result.ok is True
    assert result.attempts == 2
    assert "retry-secret-token" not in result.message


def test_daily_helpers_compute_beijing_run_times_and_cron_examples() -> None:
    schedule = scheduled_times_for_brief("2026-05-13")

    assert schedule.generate.isoformat() == "2026-05-13T17:50:00+08:00"
    assert schedule.send.isoformat() == "2026-05-13T18:10:00+08:00"

    examples = cron_examples(
        project_dir=Path("/srv/ai-rss"),
        config_path=Path("sources.yaml"),
        data_dir=Path("data"),
    )

    assert examples.timezone == "Asia/Shanghai"
    assert examples.generate == "50 17 * * * cd /srv/ai-rss && ai-rss collect --config sources.yaml --data-dir data"
    assert examples.send == "10 18 * * * cd /srv/ai-rss && ai-rss send --data-dir data"


def test_health_alerts_when_candidate_count_is_too_low() -> None:
    report = evaluate_health(candidate_count=4, source_failures=[])

    assert report.needs_alert is True
    assert report.candidate_count == 4
    assert report.reasons == ["candidate count 4 is below minimum 5"]


def test_health_alerts_when_p0_sources_fail() -> None:
    report = evaluate_health(
        candidate_count=8,
        source_failures=[
            SourceFailure(name="OpenAI Blog", priority="P0", reason="HTTP 503"),
            SourceFailure(name="Community Feed", priority="P1", reason="timeout"),
        ],
    )

    assert report.needs_alert is True
    assert report.reasons == ["P0 source failures: OpenAI Blog"]


def test_health_alert_posts_to_feishu_when_report_needs_attention(monkeypatch) -> None:
    report = evaluate_health(candidate_count=3, source_failures=[])
    webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/health-secret-token"
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", webhook)

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, webhook, json={"code": 0, "msg": "success"}, status=200)

        result = send_health_alert_to_feishu(report, brief_date="2026-05-13")
        assert len(rsps.calls) == 1
        request = rsps.calls[0].request

    assert result.ok is True
    assert "candidate count 3 is below minimum 5" in request.body.decode("utf-8")
    assert "health-secret-token" not in result.message


def test_send_cli_posts_brief_for_explicit_date(tmp_path: Path, monkeypatch) -> None:
    brief_date = "2026-05-13"
    brief_dir = tmp_path / "briefs"
    brief_dir.mkdir()
    (brief_dir / f"{brief_date}.md").write_text("# CLI Brief\n", encoding="utf-8")
    webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/cli-secret-token"
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", webhook)

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, webhook, json={"code": 0, "msg": "success"}, status=200)

        exit_code = main(["send", "--data-dir", str(tmp_path), "--date", brief_date])
        assert len(rsps.calls) == 1

    assert exit_code == 0
