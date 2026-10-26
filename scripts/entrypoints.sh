#!/usr/bin/env bash
# Run the debug API (src/) with fastapi-cli.
# Env (or .env): APP_HOST (0.0.0.0), APP_PORT (8000), APP_RELOAD (true/1 for dev reload).
set -euo pipefail
cd "$(dirname "$0")/.."

# take APP_* from .env unless already set in the environment; only these keys, so values with
# spaces or JSON elsewhere in .env are never evaluated by the shell
if [[ -f .env ]]; then
  while IFS='=' read -r key value; do
    [[ "$key" =~ ^APP_[A-Z_]+$ && -z "${!key:-}" ]] && export "$key=$value"
  done < .env
fi

APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-8000}"

args=(run --entrypoint src:app --host "$APP_HOST" --port "$APP_PORT")
[[ "${APP_RELOAD:-false}" =~ ^(1|true|True)$ ]] && args+=(--reload)

# inside the image the venv is already on PATH; locally go through uv
if command -v uv >/dev/null 2>&1 && [[ ! -x /app/.venv/bin/fastapi ]]; then
  exec uv run fastapi "${args[@]}"
fi
exec fastapi "${args[@]}"
