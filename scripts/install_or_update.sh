#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${AI_RSS_REPO_URL:-https://github.com/jeffjbyang/ai-rss.git}"
APP_DIR="${AI_RSS_APP_DIR:-/srv/ai-rss}"
BRANCH="${AI_RSS_BRANCH:-main}"

log() {
  printf '[ai-rss deploy] %s\n' "$*"
}

install_os_deps() {
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y git curl ca-certificates
  fi
}

install_uv() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
}

ensure_checkout() {
  sudo mkdir -p "$(dirname "$APP_DIR")"
  sudo chown -R "$USER:$USER" "$(dirname "$APP_DIR")"

  if [ -d "$APP_DIR/.git" ]; then
    log "Updating existing checkout at $APP_DIR"
    git -C "$APP_DIR" fetch origin "$BRANCH"
    git -C "$APP_DIR" checkout "$BRANCH"
    git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
  else
    log "Cloning $REPO_URL to $APP_DIR"
    rm -rf "$APP_DIR"
    git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
  fi
}

sync_project() {
  cd "$APP_DIR"
  uv sync --extra dev
  if [ ! -f sources.yaml ]; then
    cp sources.example.yaml sources.yaml
  fi
  if [ ! -f .env ]; then
    cp .env.example .env
    chmod 600 .env
    log "Created $APP_DIR/.env. Fill FEISHU_WEBHOOK_URL and optional AI_RSS_LLM_* values there."
  fi
  mkdir -p data/logs data/candidates data/briefs
}

install_cron() {
  local uv_bin
  uv_bin="$(command -v uv)"
  local tmp
  tmp="$(mktemp)"

  crontab -l 2>/dev/null | grep -v 'ai-rss' > "$tmp" || true
  cat >> "$tmp" <<EOF
CRON_TZ=Asia/Shanghai
50 17 * * * cd $APP_DIR && set -a && . ./.env && set +a && $uv_bin run ai-rss collect --config sources.yaml --data-dir data >> data/logs/cron.log 2>&1
10 18 * * * cd $APP_DIR && set -a && . ./.env && set +a && $uv_bin run ai-rss send --data-dir data >> data/logs/cron.log 2>&1
20 18 * * * cd $APP_DIR && git pull --ff-only origin $BRANCH && $uv_bin sync --extra dev >> data/logs/update.log 2>&1
EOF
  crontab "$tmp"
  rm -f "$tmp"
}

main() {
  install_os_deps
  install_uv
  export PATH="$HOME/.local/bin:$PATH"
  ensure_checkout
  sync_project
  install_cron
  log "Installed. Next: edit $APP_DIR/.env, then run:"
  log "cd $APP_DIR && set -a && . ./.env && set +a && uv run ai-rss collect --config sources.yaml --data-dir data"
  log "cd $APP_DIR && set -a && . ./.env && set +a && uv run ai-rss send --data-dir data"
}

main "$@"
