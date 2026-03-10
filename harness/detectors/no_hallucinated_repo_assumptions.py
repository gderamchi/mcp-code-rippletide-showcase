from __future__ import annotations

from ..models import RuleResult, ScoringContext
from .common import changed_file_paths, final_file_text, get_events


RULE_ID = '3_no_hallucinated_repo_assumptions'
STANDARD_PNPM_COMMANDS = {
    'add',
    'build',
    'dev',
    'dlx',
    'exec',
    'import',
    'install',
    'lint',
    'run',
    'test',
    'typecheck',
}


def _extract_script_name(command: str) -> str | None:
    tokens = command.split()
    if not tokens:
        return None

    if tokens[0] == 'pnpm':
        filtered = [token for token in tokens[1:] if token not in {'--dir', 'web'}]
        if not filtered:
            return None
        first = filtered[0]
        if first in STANDARD_PNPM_COMMANDS:
            return None
        return first

    if tokens[:2] == ['npm', 'run'] and len(tokens) > 2:
        return tokens[2]

    return None


def detect(context: ScoringContext, weight: int, severity: str) -> RuleResult:
    hallucinations: list[str] = []
    for event in get_events(context, 'shell_command'):
        command = event['payload']['command']
        script_name = _extract_script_name(command)
        if script_name and script_name not in context.allowed_scripts:
            hallucinations.append(f'Unknown script: {script_name}')

    for path in changed_file_paths(context):
        file_text = final_file_text(context, path)
        for pattern in context.run_request.task.disallowed_code_patterns:
            if pattern in file_text:
                hallucinations.append(f'Disallowed code pattern `{pattern}` in {path}')

    if hallucinations:
        verdict = 'fail'
        ratio = 0.0
    else:
        verdict = 'pass'
        ratio = 1.0

    return RuleResult(
        RULE_ID,
        'No hallucinated repo assumptions',
        verdict,
        ratio,
        weight,
        severity,
        hallucinations or ['No hallucinated scripts or disallowed patterns detected.'],
    )

