#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${AI_RSS_APP_DIR:-/srv/ai-rss}"

cd "$APP_DIR"
echo "== git =="
git status --short --branch
git --no-pager log --oneline -3
echo
echo "== env =="
if [ -f .env ]; then
  grep -E '^(FEISHU_WEBHOOK_URL|AI_RSS_LLM_MODEL|AI_RSS_LLM_BASE_URL)=' .env | sed 's/=.*/=<configured-or-empty>/'
else
  echo ".env missing"
fi
echo
echo "== cron =="
crontab -l | grep 'ai-rss' || true
echo
echo "== latest logs =="
ls -1 data/logs 2>/dev/null | tail -5 || true
echo
echo "== latest update log =="
tail -20 data/logs/update.log 2>/dev/null || true
