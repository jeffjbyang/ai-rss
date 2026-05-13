#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${AI_RSS_APP_DIR:-/srv/ai-rss}"
BRANCH="${AI_RSS_BRANCH:-main}"
UV_BIN="${AI_RSS_UV_BIN:-uv}"

cd "$APP_DIR"
mkdir -p data/logs

git fetch origin "$BRANCH"
current="$(git rev-parse HEAD)"
remote="$(git rev-parse "origin/$BRANCH")"

if [ "$current" = "$remote" ]; then
  printf '%s already up to date at %s\n' "$(date -Is)" "$current"
  exit 0
fi

git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"
"$UV_BIN" sync --extra dev
printf '%s updated %s -> %s\n' "$(date -Is)" "$current" "$remote"
