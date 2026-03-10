from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..models import RunRequest, RunResult
from ..observer import RunObserver
from .base import Executor


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


class ExternalProcessRunner(Executor):
    def execute(self, request: RunRequest, observer: RunObserver) -> RunResult:
        if not request.adapter_command:
            raise ValueError('External runner requires an adapter command.')

        request.output_dir.mkdir(parents=True, exist_ok=True)
        request_path = request.output_dir / 'run_request.json'
        request_path.write_text(json.dumps(_jsonable(asdict(request)), indent=2))

        command = request.adapter_command.replace('{request_file}', str(request_path))
        if command == request.adapter_command:
            command = f'{command} {request_path}'

        process = subprocess.Popen(
            shlex.split(command),
            cwd=request.workspace_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        saw_run_finished = False
        tool_categories_exposed = False
        assert process.stdout is not None
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            observer.record_existing_event(event)
            if event['event_type'] == 'run_finished':
                saw_run_finished = True
            if event['event_type'] in {'tool_call', 'file_write'}:
                tool_categories_exposed = True

        stderr_output = ''
        if process.stderr is not None:
            stderr_output = process.stderr.read()

        return_code = process.wait()
        if not saw_run_finished:
            observer.record_event(
                'run_finished',
                {
                    'status': 'completed' if return_code == 0 else 'failed',
                    'final_message': 'External adapter ended without an explicit run_finished event.',
                },
            )

        return RunResult(
            final_message='External adapter completed.',
            final_status='completed' if return_code == 0 else 'failed',
            tool_categories_exposed=tool_categories_exposed,
            metadata={'stderr': stderr_output},
        )
