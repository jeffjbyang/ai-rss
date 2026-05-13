# ai-rss deployment notes

## Server install or update

The server should pull from GitHub directly. Do not upload local build artifacts.

On the server:

```sh
curl -fsSL https://raw.githubusercontent.com/jeffjbyang/ai-rss/main/scripts/install_or_update.sh -o /tmp/ai-rss-install.sh
bash /tmp/ai-rss-install.sh
```

The installer uses these defaults:

- Repository: `https://github.com/jeffjbyang/ai-rss.git`
- App directory: `/srv/ai-rss`
- Branch: `main`

Override them when needed:

```sh
AI_RSS_REPO_URL="https://github.com/jeffjbyang/ai-rss.git" \
AI_RSS_APP_DIR="/srv/ai-rss" \
AI_RSS_BRANCH="main" \
bash /tmp/ai-rss-install.sh
```

The installer creates `/srv/ai-rss/.env` from `.env.example` if it does not exist. Keep real tokens only in that server-local file.

## Server-local configuration

Edit `/srv/ai-rss/.env` on the server:

```sh
cd /srv/ai-rss
nano .env
chmod 600 .env
```

Required for Feishu delivery:

```sh
FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/..."
```

Optional LLM provider:

```sh
AI_RSS_LLM_MODEL="your-model"
AI_RSS_LLM_BASE_URL="https://api.openai.com/v1"
AI_RSS_LLM_API_KEY="your-api-key"
```

Leave `AI_RSS_LLM_MODEL` empty to disable LLM enhancement.

## Server automation

The installer configures cron in Beijing time:

- 17:50: collect sources and generate the daily brief.
- 18:10: send the generated brief to Feishu.
- Every hour at minute 20: pull the latest `main` branch and run `uv sync`.

Check the installed state:

```sh
cd /srv/ai-rss
bash scripts/server_status.sh
```

Run the updater manually:

```sh
cd /srv/ai-rss
bash scripts/update_from_git.sh
```

Run a manual collect:

```sh
cd /srv/ai-rss
set -a && . ./.env && set +a
uv run ai-rss collect --config sources.yaml --data-dir data
cat data/logs/$(date +%F).log
```

Run a manual Feishu send after `FEISHU_WEBHOOK_URL` is configured:

```sh
cd /srv/ai-rss
set -a && . ./.env && set +a
uv run ai-rss send --data-dir data
```

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
