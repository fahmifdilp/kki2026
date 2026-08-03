#!/usr/bin/env bash
set -e
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
(cd frontend && npm install)
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
trap 'kill $BACKEND_PID 2>/dev/null || true' EXIT
(cd frontend && npm run dev)
