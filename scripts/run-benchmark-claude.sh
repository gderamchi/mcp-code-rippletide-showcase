#!/usr/bin/env bash
set -euo pipefail

.venv/bin/python -m harness.cli run-all \
  --runner external \
  --conditions condition_md condition_mcp \
  --adapter-cmd "python3 scripts/adapter_claude.py {request_file}" \
  "$@"
