from __future__ import annotations

import re
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from ..models import ScoringContext, ValidationResult


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def get_events(context: ScoringContext, event_type: str) -> list[dict[str, Any]]:
    return [event for event in context.events if event['event_type'] == event_type]


def last_event_timestamp(context: ScoringContext, event_type: str) -> str | None:
    events = get_events(context, event_type)
    if not events:
        return None
    return events[-1]['timestamp']


def validation_lookup(context: ScoringContext) -> dict[str, ValidationResult]:
    return {result.id: result for result in context.validation_results}


def final_file_text(context: ScoringContext, relative_path: str) -> str:
    return context.final_snapshot.get(relative_path, '')


def changed_file_paths(context: ScoringContext) -> list[str]:
    return [changed.path for changed in context.changed_files]


def contains_canary(value: str, canary_values: list[str]) -> bool:
    return any(token and token in value for token in canary_values)


def matches_any_regex(value: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, value) is not None for pattern in patterns)


def path_is_outside_workspace(repo_root: Path, candidate: str) -> bool:
    try:
        Path(candidate).resolve().relative_to(repo_root.resolve())
        return False
    except ValueError:
        return True
