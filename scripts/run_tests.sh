#!/usr/bin/env bash
set -euo pipefail

cd /app

PYTHONPATH="${PYTHONPATH:-}"
for d in /app/services/*/src; do [ -d "$d" ] && PYTHONPATH="${PYTHONPATH}:$d"; done
for d in /app/libs/*/src; do [ -d "$d" ] && PYTHONPATH="${PYTHONPATH}:$d"; done
export PYTHONPATH
echo "PYTHONPATH -> $PYTHONPATH"

wait_localstack() {
  url="${LOCALSTACK_URL:-http://localstack:4566}"
  echo "Waiting for LocalStack at $url ..."
  for i in {1..120}; do
    if curl -s "$url/health" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"running"|"initialized"[[:space:]]*:[[:space:]]*true'; then
      echo "LocalStack is healthy."
      return 0
    fi
    sleep 1
  done
  echo "LocalStack did not become healthy in time" >&2
  return 1
}


case "${1:-unit}" in
  unit)         exec pytest -q tests/unit ;;
  integration)  exec pytest -q tests/integration ;;
  all)          pytest -q tests/unit && exec pytest -q tests/integration ;;
  *)            exec pytest "$@" ;;
esac
