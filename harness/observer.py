from __future__ import annotations

from pathlib import Path
from typing import Any

from .logging import EventLogger, utc_now_iso


class RunObserver:
    def __init__(
        self,
        condition: str,
        logger: EventLogger,
        run_id: str,
        task_id: str,
        workspace_path: Path,
    ) -> None:
        self.condition = condition
        self.logger = logger
        self.run_id = run_id
        self.task_id = task_id
        self.workspace_path = workspace_path

    def record_event(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.logger.record(
            {
                'timestamp': utc_now_iso(),
                'run_id': self.run_id,
                'task_id': self.task_id,
                'condition': self.condition,
                'event_type': event_type,
                'payload': payload,
            }
        )

    def record_existing_event(self, event: dict[str, Any]) -> dict[str, Any]:
        envelope = {
            'timestamp': event.get('timestamp', utc_now_iso()),
            'run_id': event.get('run_id', self.run_id),
            'task_id': event.get('task_id', self.task_id),
            'condition': event.get('condition', self.condition),
            'event_type': event['event_type'],
            'payload': event.get('payload', {}),
        }
        return self.logger.record(envelope)

    def file_read(self, path: Path) -> None:
        self.record_event(
            'file_read',
            {'path': str(path.relative_to(self.workspace_path))},
        )

    def file_write(self, path: Path) -> None:
        self.record_event(
            'file_write',
            {'path': str(path.relative_to(self.workspace_path))},
        )

    def shell_command(self, command: str, cwd: Path | None = None) -> None:
        self.record_event(
            'shell_command',
            {'command': command, 'cwd': str((cwd or self.workspace_path).relative_to(self.workspace_path))},
        )

    def shell_output(self, command: str, exit_code: int, stdout: str, stderr: str) -> None:
        self.record_event(
            'shell_output',
            {
                'command': command,
                'exit_code': exit_code,
                'stdout': stdout,
                'stderr': stderr,
            },
        )

