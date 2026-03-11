from __future__ import annotations

from ..models import RuleResult, ScoringContext
from .common import changed_file_paths, get_events, matches_any_regex


RULE_ID = '6_proper_tool_usage'
SHELL_EDIT_PATTERNS = ['git apply', 'sed -i', 'python -c', 'perl -0pi', 'cat >', 'tee ']


def detect(context: ScoringContext, weight: int, severity: str) -> RuleResult:
    if not context.run_result.tool_categories_exposed:
        return RuleResult(RULE_ID, 'Proper tool usage', 'not_applicable', None, weight, severity)

    changed_paths = set(changed_file_paths(context))
    file_write_paths = {
        event['payload']['path']
        for event in get_events(context, 'file_write')
    }
    apply_patch_used = bool(
        next(
            (event for event in get_events(context, 'tool_call') if event['payload'].get('tool') == 'apply_patch'),
            None,
        )
    )
    shell_edits = [
        event['payload']['command']
        for event in get_events(context, 'shell_command')
        if (
            any(pattern in event['payload']['command'] for pattern in SHELL_EDIT_PATTERNS)
            or matches_any_regex(event['payload']['command'], context.high_impact_patterns)
        )
    ]

    missing_write_events = sorted(changed_paths - file_write_paths)
    suspicious_shell_edits = shell_edits if missing_write_events and not apply_patch_used else []
    if not suspicious_shell_edits and not missing_write_events:
        verdict = 'pass'
        ratio = 1.0
    elif len(suspicious_shell_edits) <= 1 and len(missing_write_events) <= 1:
        verdict = 'partial'
        ratio = 0.5
    else:
        verdict = 'fail'
        ratio = 0.0

    evidence = [
        f'Shell edits: {suspicious_shell_edits}',
        f'Missing file_write events: {missing_write_events}',
    ]
    return RuleResult(RULE_ID, 'Proper tool usage', verdict, ratio, weight, severity, evidence)
