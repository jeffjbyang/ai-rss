from __future__ import annotations

from dataclasses import dataclass
from os import getenv
from pathlib import Path
from time import sleep

import requests


DEFAULT_WEBHOOK_ENV = "FEISHU_WEBHOOK_URL"


@dataclass(frozen=True)
class NotifyResult:
    ok: bool
    attempts: int
    message: str


def send_brief_to_feishu(
    data_dir: Path,
    brief_date: str,
    *,
    webhook_env: str = DEFAULT_WEBHOOK_ENV,
    max_attempts: int = 2,
    retry_delay_seconds: float = 0.0,
    timeout: float = 10.0,
) -> NotifyResult:
    brief_path = data_dir / "briefs" / f"{brief_date}.md"
    brief = brief_path.read_text(encoding="utf-8")
    return send_text_to_feishu(
        brief,
        webhook_env=webhook_env,
        max_attempts=max_attempts,
        retry_delay_seconds=retry_delay_seconds,
        timeout=timeout,
    )


def send_text_to_feishu(
    text: str,
    *,
    webhook_env: str = DEFAULT_WEBHOOK_ENV,
    max_attempts: int = 2,
    retry_delay_seconds: float = 0.0,
    timeout: float = 10.0,
) -> NotifyResult:
    webhook = getenv(webhook_env)
    if not webhook:
        return NotifyResult(ok=False, attempts=0, message=f"{webhook_env} is not configured")

    payload = {"msg_type": "text", "content": {"text": text}}
    attempts = max(1, max_attempts)
    last_error = "unknown failure"

    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(webhook, json=payload, timeout=timeout)
        except requests.RequestException as exc:
            last_error = exc.__class__.__name__
        else:
            if response.status_code >= 400:
                last_error = f"HTTP {response.status_code}"
            else:
                try:
                    body = response.json()
                except ValueError:
                    body = {}
                if int(body.get("code", 0)) == 0:
                    return NotifyResult(ok=True, attempts=attempt, message="Feishu brief sent")
                last_error = f"Feishu code {body.get('code')}"

        if attempt < attempts and retry_delay_seconds > 0:
            sleep(retry_delay_seconds)

    return NotifyResult(ok=False, attempts=attempts, message=f"Feishu webhook failed after {attempts} attempts: {last_error}")
