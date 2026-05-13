# ai-rss

Daily AI technology brief generator for tracking AI engineering, AI coding, Agentic Coding, and software delivery practice signals.

## What It Does

- Collects RSS, GitHub search/release, arXiv, and Hacker News style sources.
- Stores candidates in SQLite.
- Generates `candidates/YYYY-MM-DD.md`, `candidates/YYYY-MM-DD.json`, and a default `briefs/YYYY-MM-DD.md`.
- Scores and sections the brief with priority for AI coding / software delivery topics while keeping exploratory AI signals.
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
