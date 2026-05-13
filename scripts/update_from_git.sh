#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${AI_RSS_APP_DIR:-/srv/ai-rss}"
BRANCH="${AI_RSS_BRANCH:-main}"
UV_BIN="${AI_RSS_UV_BIN:-uv}"
FETCH_TIMEOUT_SECONDS="${AI_RSS_FETCH_TIMEOUT_SECONDS:-45}"
FALLBACK_REPO_URLS="${AI_RSS_FALLBACK_REPO_URLS:-https://ghfast.top/https://github.com/jeffjbyang/ai-rss.git https://gh.llkk.cc/https://github.com/jeffjbyang/ai-rss.git https://gh-proxy.com/https://github.com/jeffjbyang/ai-rss.git}"

cd "$APP_DIR"
mkdir -p data/logs

fetch_branch() {
  local remote_ref="$1"
  local label="$2"
  printf '%s fetching %s\n' "$(date -Is)" "$label"
  timeout "$FETCH_TIMEOUT_SECONDS" git fetch "$remote_ref" "$BRANCH"
}

if ! fetch_branch origin origin; then
  fetched=0
  for repo_url in $FALLBACK_REPO_URLS; do
    if fetch_branch "$repo_url" "$repo_url"; then
      fetched=1
      break
    fi
  done
  if [ "$fetched" -ne 1 ]; then
    printf '%s failed to fetch %s from origin and fallbacks\n' "$(date -Is)" "$BRANCH" >&2
    exit 1
  fi
fi

current="$(git rev-parse HEAD)"
remote="$(git rev-parse FETCH_HEAD)"

if [ "$current" = "$remote" ]; then
  printf '%s already up to date at %s\n' "$(date -Is)" "$current"
  exit 0
fi

git checkout "$BRANCH"
git merge --ff-only FETCH_HEAD
"$UV_BIN" sync --extra dev
printf '%s updated %s -> %s\n' "$(date -Is)" "$current" "$remote"
