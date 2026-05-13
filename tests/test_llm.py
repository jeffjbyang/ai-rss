import responses

from ai_rss.llm import OpenAICompatibleLLMClient, llm_client_from_env
from ai_rss.models import Item


def test_openai_compatible_client_turns_chat_completion_json_into_enhancement() -> None:
    client = OpenAICompatibleLLMClient(
        model="test-model",
        base_url="https://llm.example.com/v1",
        api_key="secret-key",
    )

    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://llm.example.com/v1/chat/completions",
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"summary":"增强摘要","key_changes":"关键变化","why_matters":"重要性","practical_takeaway":"启发"}'
                        }
                    }
                ]
            },
            status=200,
        )

        enhancement = client.enhance(_item())
        request = rsps.calls[0].request

    assert request.headers["Authorization"] == "Bearer secret-key"
    assert b'"model": "test-model"' in request.body
    assert enhancement.summary == "增强摘要"
    assert enhancement.key_changes == "关键变化"
    assert enhancement.why_matters == "重要性"
    assert enhancement.practical_takeaway == "启发"


def test_llm_client_from_env_requires_model_and_endpoint_or_key(monkeypatch) -> None:
    monkeypatch.delenv("AI_RSS_LLM_MODEL", raising=False)
    monkeypatch.delenv("AI_RSS_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("AI_RSS_LLM_API_KEY", raising=False)

    assert llm_client_from_env() is None

    monkeypatch.setenv("AI_RSS_LLM_MODEL", "local-model")
    monkeypatch.setenv("AI_RSS_LLM_BASE_URL", "http://localhost:11434/v1")

    assert llm_client_from_env() is not None


def _item() -> Item:
    return Item(
        title="GitHub ships coding agent",
        source_name="GitHub Blog",
        source_type="rss",
        source_priority="P0",
        url="https://example.com",
        canonical_url="https://example.com",
        published_at="2026-05-14T08:00:00+00:00",
        summary="Official release for coding agents.",
        tags=["ai-coding"],
    )
