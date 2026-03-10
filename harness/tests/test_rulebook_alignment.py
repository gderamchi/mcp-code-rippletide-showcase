from pathlib import Path

from harness.detectors import RULE_DETECTORS
from harness.scoring import load_rulebook
from harness.task_loader import load_policy


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_rulebook_matches_policy_and_detectors() -> None:
    rulebook = load_rulebook(REPO_ROOT)
    policy = load_policy(REPO_ROOT)

    assert len(rulebook) == 10
    assert {rule['rule_id'] for rule in rulebook} == set(policy['score_weights'])
    assert {rule['rule_id'] for rule in rulebook} == set(RULE_DETECTORS)

    for rule in rulebook:
        assert rule['weight'] == policy['score_weights'][rule['rule_id']]
        if rule['severity'] == 'hard':
            assert rule['rule_id'] in policy['hard_rules']
        else:
            assert rule['rule_id'] not in policy['hard_rules']

