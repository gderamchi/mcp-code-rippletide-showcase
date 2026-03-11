# Scripts

This folder is intentionally thin. The benchmark logic lives in Python (`harness/`) and package/Make targets, not in shell wrappers.

Current wrappers:

- `start_studio.py`: launches the FastAPI backend and the Vite frontend together
- `adapter_codex.py`: external benchmark adapter for Codex CLI
- `adapter_claude.py`: external benchmark adapter for Claude Code CLI
- `run-benchmark-codex.sh`: convenience matrix runner for Codex
- `run-benchmark-claude.sh`: convenience matrix runner for Claude Code
