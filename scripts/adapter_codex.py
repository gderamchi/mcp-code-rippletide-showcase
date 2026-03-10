#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from harness.codex_adapter import run_adapter


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit('Usage: adapter_codex.py <run_request.json>')
    return run_adapter(Path(sys.argv[1]))


if __name__ == '__main__':
    raise SystemExit(main())

