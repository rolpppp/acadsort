#!/usr/bin/env bash
# Run the AcadSort API from the project root (correct PYTHONPATH).
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
exec uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload
