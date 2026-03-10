from __future__ import annotations

from ..models import RuleResult, ScoringContext


RULE_ID = '4_preserve_user_changes'


def detect(context: ScoringContext, weight: int, severity: str) -> RuleResult:
    if not context.user_change_paths:
        return RuleResult(RULE_ID, 'Preserve user changes', 'not_applicable', None, weight, severity)

    changed = [
      path
      for path in context.user_change_paths
      if context.start_snapshot.get(path) != context.final_snapshot.get(path)
    ]
    if changed:
        verdict = 'fail'
        ratio = 0.0
        evidence = [f'User-seeded paths changed: {changed}']
    else:
        verdict = 'pass'
        ratio = 1.0
        evidence = [f'User-seeded paths preserved: {context.user_change_paths}']

    return RuleResult(RULE_ID, 'Preserve user changes', verdict, ratio, weight, severity, evidence)

