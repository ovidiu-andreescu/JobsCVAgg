#!/usr/bin/env bash
set -euo pipefail

cd /app

PYTHONPATH="${PYTHONPATH:-}"
for d in /app/services/*/src; do [ -d "$d" ] && PYTHONPATH="${PYTHONPATH}:$d"; done
for d in /app/libs/*/src; do [ -d "$d" ] && PYTHONPATH="${PYTHONPATH}:$d"; done
export PYTHONPATH
echo "PYTHONPATH -> $PYTHONPATH"




case "${1:-unit}" in
  unit)         exec pytest -v -rA --durations=10 tests/unit ;;
  integration)  exec pytest -v -rA --durations=10 tests/integration ;;
  all)          pytest -v -rA tests/unit; exec pytest -v -Ra tests/integration ;;
  *)            exec pytest "$@" ;;
esac
