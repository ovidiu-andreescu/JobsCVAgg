#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-unit}"

PYTHONPATH="${PYTHONPATH:-}"
if [ -d /app/libs ]; then
  for d in /app/libs/*/src; do [ -d "$d" ] && PYTHONPATH="${PYTHONPATH}:$d"; done
fi
for d in /app/services/*/src; do [ -d "$d" ] && PYTHONPATH="${PYTHONPATH}:$d"; done
export PYTHONPATH

echo "PYTHONPATH -> $PYTHONPATH"

case "$TARGET" in
  unit)
    exec pytest -m "unit" -q
    ;;
  integration)
    exec pytest -m "integration" -q
    ;;
  all)
    pytest -m "unit" -q
    exec pytest -m "integration" -q
    ;;
  *)
    exec pytest "$@"
    ;;
esac
