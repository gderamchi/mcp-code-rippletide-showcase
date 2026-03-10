#!/usr/bin/env bash
set -euo pipefail

.venv/bin/python -m harness.cli run-all --runner demo --conditions condition_md condition_mcp "$@"

