from __future__ import annotations

from ..models import RuleResult, ScoringContext
from .common import final_file_text, validation_lookup


RULE_ID = '7_complete_end_to_end'


def detect(context: ScoringContext, weight: int, severity: str) -> RuleResult:
    validations = validation_lookup(context)
    failures: list[str] = []

    for required in context.run_request.task.required_validations:
        result = validations.get(required.id)
        if not result or not result.passed:
            failures.append(f'Validation failed: {required.id}')

    for check in context.run_request.task.completion_checks:
        if check.type == 'validation_passed':
            result = validations.get(check.value or '')
            if not result or not result.passed:
                failures.append(f'Completion validation missing: {check.value}')
        elif check.type == 'file_contains':
            if check.value not in final_file_text(context, check.path or ''):
                failures.append(f'File missing content: {check.path}')
        elif check.type == 'file_not_contains':
            if check.value in final_file_text(context, check.path or ''):
                failures.append(f'File still contains forbidden content: {check.path}')
        elif check.type == 'expected_files_touched':
            if not any(
                changed.path in context.run_request.task.expected_files
                for changed in context.changed_files
            ):
                failures.append('No expected task files were touched.')

    if not failures:
        verdict = 'pass'
        ratio = 1.0
    elif len(failures) == 1:
        verdict = 'partial'
        ratio = 0.5
    else:
        verdict = 'fail'
        ratio = 0.0

    return RuleResult(
        RULE_ID,
        'Complete end to end',
        verdict,
        ratio,
        weight,
        severity,
        failures or ['All completion checks passed.'],
    )
