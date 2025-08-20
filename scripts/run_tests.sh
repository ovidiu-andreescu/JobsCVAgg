#!/usr/bin/env bash
set -euo pipefail

cd /app

PYTHONPATH="${PYTHONPATH:-}"
for d in /app/services/*/src; do [ -d "$d" ] && PYTHONPATH="${PYTHONPATH}:$d"; done
for d in /app/libs/*/src; do [ -d "$d" ] && PYTHONPATH="${PYTHONPATH}:$d"; done
export PYTHONPATH
echo "PYTHONPATH -> $PYTHONPATH"

case "${1:-unit}" in
  unit)         exec pytest -q tests/unit ;;
  integration)  exec pytest -q tests/integration ;;
  all)          pytest -q tests/unit && exec pytest -q tests/integration ;;
  *)            exec pytest "$@" ;;
esac
