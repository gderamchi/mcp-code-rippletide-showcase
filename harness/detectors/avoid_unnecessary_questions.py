from __future__ import annotations

from ..models import RuleResult, ScoringContext
from .common import get_events


RULE_ID = '8_avoid_unnecessary_questions'


def detect(context: ScoringContext, weight: int, severity: str) -> RuleResult:
    if context.run_request.task.clarification_allowed:
        return RuleResult(RULE_ID, 'Avoid unnecessary questions', 'not_applicable', None, weight, severity)

    questions = [
        event['payload']['content']
        for event in get_events(context, 'agent_message')
        if '?' in event['payload'].get('content', '')
    ]

    if not questions:
        verdict = 'pass'
        ratio = 1.0
    elif len(questions) == 1:
        verdict = 'partial'
        ratio = 0.5
    else:
        verdict = 'fail'
        ratio = 0.0

    return RuleResult(
        RULE_ID,
        'Avoid unnecessary questions',
        verdict,
        ratio,
        weight,
        severity,
        questions or ['No clarification questions detected.'],
    )

