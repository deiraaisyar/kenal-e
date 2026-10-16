#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -x be/.venv/bin/python || ! -d fe/node_modules ]]; then
  echo "Dependensi belum terpasang. Ikuti instalasi awal di README.md."
  exit 1
fi
backend_pid=''
frontend_pid=''
cleanup() {
  trap - EXIT INT TERM
  if [[ -n "$backend_pid" ]]; then kill "$backend_pid" 2>/dev/null || true; fi
  if [[ -n "$frontend_pid" ]]; then kill -- "-$frontend_pid" 2>/dev/null || kill "$frontend_pid" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM
be/.venv/bin/python -m uvicorn be.app:app --host 127.0.0.1 --port 8000 --reload &
backend_pid=$!
setsid npm --prefix fe run dev -- --host 127.0.0.1 &
frontend_pid=$!
echo "Kenal-E: http://localhost:5173 — API: http://localhost:8000/docs"
wait -n "$backend_pid" "$frontend_pid"
