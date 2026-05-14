from __future__ import annotations

import json
from dataclasses import dataclass
from os import getenv
from pathlib import Path
from time import sleep

import requests


DEFAULT_WEBHOOK_ENV = "FEISHU_WEBHOOK_URL"
MAX_FEISHU_TEXT_BYTES = 30_000
FEISHU_KEYWORD = "AI 技术简报"


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

    chunks = split_text_for_feishu(text)
    attempts = max(1, max_attempts)
    total_attempts = 0

    for index, chunk in enumerate(chunks, start=1):
        ok, chunk_attempts, last_error = _post_text_chunk(
            webhook,
            chunk,
            attempts=attempts,
            retry_delay_seconds=retry_delay_seconds,
            timeout=timeout,
        )
        total_attempts += chunk_attempts
        if not ok:
            return NotifyResult(
                ok=False,
                attempts=total_attempts,
                message=f"Feishu webhook failed on chunk {index}/{len(chunks)} after {chunk_attempts} attempts: {last_error}",
            )

    if len(chunks) == 1:
        return NotifyResult(ok=True, attempts=total_attempts, message="Feishu brief sent")
    return NotifyResult(ok=True, attempts=total_attempts, message=f"Feishu brief sent in {len(chunks)} chunks")


def split_text_for_feishu(text: str, *, max_bytes: int = MAX_FEISHU_TEXT_BYTES) -> list[str]:
    if _payload_size(text) <= max_bytes:
        return [text]

    chunks: list[str] = []
    current = ""
    for part in _line_parts(text):
        candidate = part if not current else current + "\n" + part
        if _payload_size(_with_chunk_header(candidate, 1, 1)) <= max_bytes:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        if _payload_size(_with_chunk_header(part, 1, 1)) <= max_bytes:
            current = part
            continue
        chunks.extend(_split_oversized_part(part, max_bytes=max_bytes))

    if current:
        chunks.append(current)

    total = len(chunks)
    return [_with_chunk_header(chunk, index, total) for index, chunk in enumerate(chunks, start=1)]


def _post_text_chunk(
    webhook: str,
    text: str,
    *,
    attempts: int,
    retry_delay_seconds: float,
    timeout: float,
) -> tuple[bool, int, str]:
    last_error = "unknown failure"

    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(
                webhook,
                data=_payload_bytes(text),
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=timeout,
            )
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
                    return True, attempt, "success"
                last_error = f"Feishu code {body.get('code')}"

        if attempt < attempts and retry_delay_seconds > 0:
            sleep(retry_delay_seconds)

    return False, attempts, last_error


def _line_parts(text: str) -> list[str]:
    return text.splitlines()


def _split_oversized_part(part: str, *, max_bytes: int) -> list[str]:
    pieces: list[str] = []
    current = ""
    for char in part:
        candidate = current + char
        if _payload_size(_with_chunk_header(candidate, 1, 1)) <= max_bytes:
            current = candidate
            continue
        if current:
            pieces.append(current)
        current = char
    if current:
        pieces.append(current)
    return pieces


def _with_chunk_header(text: str, index: int, total: int) -> str:
    header = f"{FEISHU_KEYWORD} ({index}/{total})"
    return f"{header}\n\n{text}"


def _payload_size(text: str) -> int:
    return len(_payload_bytes(text))


def _payload_bytes(text: str) -> bytes:
    payload = {"msg_type": "text", "content": {"text": text}}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
