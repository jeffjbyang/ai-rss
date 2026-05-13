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
