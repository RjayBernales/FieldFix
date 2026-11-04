#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python -m pytest -q
npm --prefix frontend run build
.venv/bin/python scripts/secret_scan.py
