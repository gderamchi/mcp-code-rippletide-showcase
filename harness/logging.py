from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class EventLogger:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._events: list[dict[str, Any]] = []

    @property
    def events(self) -> list[dict[str, Any]]:
        return list(self._events)

    def record(self, event: dict[str, Any]) -> dict[str, Any]:
        with self.log_path.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(event, ensure_ascii=True) + '\n')
        self._events.append(event)
        return event

