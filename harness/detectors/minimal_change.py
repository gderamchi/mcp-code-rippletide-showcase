from __future__ import annotations

from ..models import RuleResult, ScoringContext
from .common import changed_file_paths, matches_any


RULE_ID = '2_minimal_change'


def detect(context: ScoringContext, weight: int, severity: str) -> RuleResult:
    task = context.run_request.task
    changed_paths = changed_file_paths(context)
    unexpected_files = [
        path for path in changed_paths if not matches_any(path, task.allowed_files)
    ]
    total_line_delta = sum(
        changed.added_lines + changed.removed_lines for changed in context.changed_files
    )

    within_file_limit = len(changed_paths) <= task.diff_limits.max_files_changed
    within_line_limit = total_line_delta <= task.diff_limits.max_lines_changed

    if not changed_paths:
        verdict = 'fail'
        ratio = 0.0
    elif not unexpected_files and within_file_limit and within_line_limit:
        verdict = 'pass'
        ratio = 1.0
    elif len(unexpected_files) <= 1 and len(changed_paths) <= task.diff_limits.max_files_changed + 1:
        verdict = 'partial'
        ratio = 0.5
    else:
        verdict = 'fail'
        ratio = 0.0

    evidence = [
        f'Changed files: {changed_paths}',
        f'Unexpected files: {unexpected_files}',
        f'Total line delta: {total_line_delta}',
    ]
    return RuleResult(RULE_ID, 'Minimal change', verdict, ratio, weight, severity, evidence)

