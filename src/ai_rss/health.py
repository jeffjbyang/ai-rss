from __future__ import annotations

from dataclasses import dataclass

from .notify import NotifyResult, send_text_to_feishu


@dataclass(frozen=True)
class SourceFailure:
    name: str
    priority: str
    reason: str = ""


@dataclass(frozen=True)
class HealthReport:
    candidate_count: int
    source_failures: list[SourceFailure]
    reasons: list[str]

    @property
    def needs_alert(self) -> bool:
        return bool(self.reasons)


def evaluate_health(
    *,
    candidate_count: int,
    source_failures: list[SourceFailure],
    minimum_candidates: int = 5,
) -> HealthReport:
    reasons = []
    if candidate_count < minimum_candidates:
        reasons.append(f"candidate count {candidate_count} is below minimum {minimum_candidates}")
    p0_failures = [failure.name for failure in source_failures if failure.priority.upper() == "P0"]
    if p0_failures:
        reasons.append(f"P0 source failures: {', '.join(p0_failures)}")

    return HealthReport(candidate_count=candidate_count, source_failures=source_failures, reasons=reasons)


def send_health_alert_to_feishu(report: HealthReport, *, brief_date: str) -> NotifyResult:
    if not report.needs_alert:
        return NotifyResult(ok=True, attempts=0, message="Health ok; no alert sent")

    lines = [
        f"AI RSS health alert - {brief_date}",
        f"candidate_count: {report.candidate_count}",
        "",
        "Reasons:",
    ]
    lines.extend(f"- {reason}" for reason in report.reasons)
    return send_text_to_feishu("\n".join(lines))
