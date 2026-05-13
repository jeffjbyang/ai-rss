from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Protocol

import requests

from .models import Item


@dataclass(frozen=True)
class LLMEnhancement:
    summary: str = ""
    key_changes: str = ""
    why_matters: str = ""
    practical_takeaway: str = ""


class LLMClient(Protocol):
    def enhance(self, item: Item) -> LLMEnhancement: ...


class OpenAICompatibleLLMClient:
    def __init__(
        self,
        *,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        timeout: float = 30.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def enhance(self, item: Item) -> LLMEnhancement:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self._headers(),
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是面向后台开发者的 AI 技术简报编辑。"
                            "只输出 JSON，不要 Markdown，不要解释。"
                        ),
                    },
                    {"role": "user", "content": _prompt(item)},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        return _enhancement_from_json(content)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


def llm_client_from_env() -> LLMClient | None:
    model = os.getenv("AI_RSS_LLM_MODEL", "").strip()
    base_url = os.getenv("AI_RSS_LLM_BASE_URL", "").strip()
    api_key = os.getenv("AI_RSS_LLM_API_KEY", "").strip()
    if not model:
        return None
    if not base_url and not api_key:
        return None
    return OpenAICompatibleLLMClient(
        model=model,
        base_url=base_url or "https://api.openai.com/v1",
        api_key=api_key,
    )


def _prompt(item: Item) -> str:
    return json.dumps(
        {
            "task": "为每日 AI 技术简报增强这条候选内容。",
            "requirements": {
                "summary": "一句中文摘要，80 字以内。",
                "key_changes": "具体发生了什么，120 字以内。",
                "why_matters": "为什么对 AI 技术、后台开发或工程实践重要，120 字以内。",
                "practical_takeaway": "仅当与 AI coding/软件交付相关时给可落地启发，否则留空。",
            },
            "output_schema": {
                "summary": "string",
                "key_changes": "string",
                "why_matters": "string",
                "practical_takeaway": "string",
            },
            "item": {
                "title": item.title,
                "source": item.source_name,
                "url": item.url,
                "summary": item.summary,
                "tags": item.tags,
            },
        },
        ensure_ascii=False,
    )


def _enhancement_from_json(content: str) -> LLMEnhancement:
    data = json.loads(_strip_fences(content))
    return LLMEnhancement(
        summary=str(data.get("summary") or ""),
        key_changes=str(data.get("key_changes") or ""),
        why_matters=str(data.get("why_matters") or ""),
        practical_takeaway=str(data.get("practical_takeaway") or ""),
    )


def _strip_fences(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text
