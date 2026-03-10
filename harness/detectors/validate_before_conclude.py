from __future__ import annotations

from ..models import RuleResult, ScoringContext
from .common import get_events


RULE_ID = '1_validate_before_conclude'


def detect(context: ScoringContext, weight: int, severity: str) -> RuleResult:
    required_commands = {validation.command for validation in context.run_request.task.required_validations}
    if not required_commands:
        return RuleResult(RULE_ID, 'Validate before conclude', 'not_applicable', None, weight, severity)

    shell_outputs = {
        event['payload']['command']: event['payload']
        for event in get_events(context, 'shell_output')
    }
    shell_commands = get_events(context, 'shell_command')
    completion_timestamp = (
        next(
            (
                event['timestamp']
                for event in reversed(get_events(context, 'agent_message'))
                if event['payload'].get('final')
            ),
            None,
        )
        or next(
            (event['timestamp'] for event in reversed(get_events(context, 'run_finished'))),
            None,
        )
    )
    last_file_write = next(
        (event['timestamp'] for event in reversed(get_events(context, 'file_write'))),
        None,
    )

    successful_commands: list[str] = []
    for event in shell_commands:
        command = event['payload']['command']
        if command not in required_commands:
            continue
        if last_file_write and event['timestamp'] < last_file_write:
            continue
        if completion_timestamp and event['timestamp'] > completion_timestamp:
            continue
        result = shell_outputs.get(command)
        if result and result['exit_code'] == 0:
            successful_commands.append(command)

    if len(successful_commands) == len(required_commands):
        verdict = 'pass'
        ratio = 1.0
    elif successful_commands:
        verdict = 'partial'
        ratio = 0.5
    else:
        verdict = 'fail'
        ratio = 0.0

    evidence = [f'Validated commands: {successful_commands or ["none"]}']
    return RuleResult(RULE_ID, 'Validate before conclude', verdict, ratio, weight, severity, evidence)

