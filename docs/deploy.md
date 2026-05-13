# ai-rss deployment notes

## Feishu webhook

Set the Feishu bot webhook as an environment variable on the host that runs cron:

```sh
export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/..."
```

The sender reads `briefs/YYYY-MM-DD.md` under the configured data directory and posts it as a Feishu text message. Failed Feishu requests are retried once by default, and command output only reports sanitized status messages.

Manual send example:

```sh
ai-rss send --data-dir data --date 2026-05-13
```

## Beijing daily schedule

The MVP schedule is based on Beijing time:

- 17:50: generate candidates/default brief for the day.
- 18:10: send `briefs/YYYY-MM-DD.md` to Feishu.

Cron example:

```cron
CRON_TZ=Asia/Shanghai
50 17 * * * cd /srv/ai-rss && ai-rss collect --config sources.yaml --data-dir data
10 18 * * * cd /srv/ai-rss && ai-rss send --data-dir data
```

If the system cron does not support `CRON_TZ`, configure the server timezone to `Asia/Shanghai` or wrap the command in the host's preferred timezone mechanism.

## Health alerts

Health reporting should alert when either condition is true:

- Candidate count is below 5.
- Any P0 source fails.

Health alert messages use the same `FEISHU_WEBHOOK_URL` configuration and include the alert reasons without printing webhook secrets.

## Optional LLM enhancement

LLM enhancement is optional. The daily brief still works without it.

Configure an OpenAI-compatible provider with environment variables:

```sh
export AI_RSS_LLM_MODEL="your-model"
export AI_RSS_LLM_BASE_URL="https://api.openai.com/v1"
export AI_RSS_LLM_API_KEY="your-api-key"
```

For a local provider that does not require a key:

```sh
export AI_RSS_LLM_MODEL="qwen2.5:7b"
export AI_RSS_LLM_BASE_URL="http://localhost:11434/v1"
unset AI_RSS_LLM_API_KEY
```

Only selected brief candidates are enhanced. If the provider times out or returns an error, generation falls back to the rule-based summary for that item.

Check the daily run log to confirm whether LLM was used:

```sh
cat data/logs/$(date +%F).log
```

The log includes:

```text
llm_enabled=true
llm_attempted=15
llm_succeeded=13
llm_failed=2
```
