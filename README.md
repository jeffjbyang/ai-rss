# ai-rss

Daily AI technology brief generator for tracking AI engineering, AI coding, Agentic Coding, and software delivery practice signals.

## What It Does

- Collects RSS, GitHub search/release, arXiv, and Hacker News style sources.
- Stores candidates in SQLite.
- Generates `candidates/YYYY-MM-DD.md`, `candidates/YYYY-MM-DD.json`, and a default `briefs/YYYY-MM-DD.md`.
- Scores and sections the brief with priority for AI coding / software delivery topics while keeping exploratory AI signals.
- Optionally enhances selected brief items with an OpenAI-compatible LLM provider.
- Sends the final Markdown brief to a Feishu group bot.
- Records source failures and low-candidate health signals in `logs/YYYY-MM-DD.log`.

## Local Setup

```sh
uv sync --extra dev
cp sources.example.yaml sources.yaml
```

Run tests:

```sh
uv run --extra dev pytest -q
```

Generate candidates and the default brief:

```sh
uv run ai-rss collect --config sources.yaml --data-dir data
```

## Optional LLM Enhancement

LLM enhancement is disabled unless a model and either a base URL or API key are configured. When enabled, the system enhances selected brief items with:

- Chinese summary
- Key changes
- Why it matters
- Practical takeaway for AI coding / software delivery items

If the LLM call fails, the brief falls back to the rule-based text and still generates.

OpenAI-compatible configuration:

```sh
export AI_RSS_LLM_MODEL="your-model"
export AI_RSS_LLM_BASE_URL="https://api.openai.com/v1"
export AI_RSS_LLM_API_KEY="your-api-key"
uv run ai-rss collect --config sources.yaml --data-dir data
```

After each collect run, confirm whether LLM enhancement was used in the daily log:

```sh
cat data/logs/$(date +%F).log
```

Expected fields:

```text
llm_enabled=true
llm_attempted=15
llm_succeeded=15
llm_failed=0
```

If LLM is not configured, the log shows:

```text
llm_enabled=false
llm_attempted=0
llm_succeeded=0
llm_failed=0
```

Local OpenAI-compatible endpoint example:

```sh
export AI_RSS_LLM_MODEL="qwen2.5:7b"
export AI_RSS_LLM_BASE_URL="http://localhost:11434/v1"
unset AI_RSS_LLM_API_KEY
uv run ai-rss collect --config sources.yaml --data-dir data
```

Send a generated brief to Feishu:

```sh
export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/..."
uv run ai-rss send --data-dir data
```

## Daily Schedule

The MVP schedule uses Beijing time:

- 17:50: collect sources, generate candidates, generate default brief.
- 18:10: send `briefs/YYYY-MM-DD.md`.

Cron example:

```cron
CRON_TZ=Asia/Shanghai
50 17 * * * cd /srv/ai-rss && uv run ai-rss collect --config sources.yaml --data-dir data
10 18 * * * cd /srv/ai-rss && uv run ai-rss send --data-dir data
```

## Review Flow

At 17:50 the system writes a default brief to:

```text
data/briefs/YYYY-MM-DD.md
```

You can edit that file before 18:10. The send command reads the Markdown file as-is.

## Docs

- [PRD](AI_TECH_BRIEF_PRD.md)
- [MVP issues](ISSUES.md)
- [Deployment notes](docs/deploy.md)
