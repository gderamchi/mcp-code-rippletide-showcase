#!/usr/bin/env python3
from __future__ import annotations

import signal
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def start_process(command: list[str]) -> subprocess.Popen[str]:
    return subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        text=True,
    )


def main() -> int:
    backend = start_process(
        ['.venv/bin/python', '-m', 'uvicorn', 'harness.server.app:app', '--reload', '--port', '8008']
    )
    frontend = start_process(['pnpm', '--dir', 'web', 'dev'])
    processes = [backend, frontend]

    def shutdown(*_args) -> None:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print('Dynamic Benchmark Studio')
    print('Backend: http://127.0.0.1:8008')
    print('Frontend: http://localhost:5173/studio')
    print('Press Ctrl+C to stop both processes.')

    try:
        while True:
            for process in processes:
                return_code = process.poll()
                if return_code is not None:
                    shutdown()
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
