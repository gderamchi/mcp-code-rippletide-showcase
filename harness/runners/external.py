from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

from ..models import RunRequest, RunResult
from ..observer import RunObserver


class ExternalProcessRunner:
    def __init__(self, command: str) -> None:
        self.command = command

    def execute(self, request: RunRequest, observer: RunObserver) -> RunResult:
        request_path = request.workspace / "run_request.json"
        request_path.write_text(json.dumps(request.as_json(), indent=2), encoding="utf-8")

        process = subprocess.Popen(
            [*shlex.split(self.command), str(request_path)],
            cwd=request.workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        final_message = "external adapter finished"
        status = "completed"

        assert process.stdout is not None
        for line in process.stdout:
          line = line.strip()
          if not line:
              continue
          payload = json.loads(line)
          event_type = payload.pop("event_type")
          observer.record_event(event_type, payload)
          if event_type == "run_finished":
              final_message = payload.get("final_message", final_message)
              status = payload.get("status", status)

        stderr = process.stderr.read() if process.stderr is not None else ""
        exit_code = process.wait()
        if stderr:
            observer.record_event("shell_output", {"channel": "stderr", "output": stderr, "exit_code": exit_code})
        return RunResult(status=status if exit_code == 0 else "failed", final_message=final_message)
