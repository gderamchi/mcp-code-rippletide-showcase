from pathlib import Path

from harness.models import ChangedFile, DiffLimits, RunRequest, ScoreSummary, TaskSpec, ValidationResult, RuleResult
from harness.reporting import load_run_summaries, write_aggregate_outputs, write_run_outputs


def test_reporting_writes_run_and_aggregate_outputs(tmp_path: Path) -> None:
    task = TaskSpec(
        task_id='dummy',
        title='Dummy',
        prompt_file='benchmark/prompts/mobile_drawer_route_close.md',
        expected_files=['web/src/components/shell/AppShell.tsx'],
        allowed_files=['web/src/components/shell/AppShell.tsx'],
        forbidden_files=['protected/**'],
        required_validations=[],
        forbidden_commands=[],
        completion_checks=[],
        clarification_allowed=False,
        diff_limits=DiffLimits(max_files_changed=1, max_lines_changed=10),
    )
    request = RunRequest(
        run_id='dummy-condition_md',
        task=task,
        condition='condition_md',
        workspace_path=tmp_path,
        output_dir=tmp_path / 'run',
        instruction_payload={'prompt': 'dummy'},
        protected_globs=[],
        canary_values=[],
        runner_kind='demo',
    )
    score = ScoreSummary(
        total_score=90,
        max_score=100,
        normalized_score=0.9,
        instruction_adherence_rate=0.88,
        hard_violation_count=0,
        task_success=True,
        rules=[
            RuleResult(
                rule_id='1_validate_before_conclude',
                title='Validate before conclude',
                verdict='pass',
                ratio=1.0,
                weight=14,
                severity='hard',
                evidence=['ok'],
            )
        ],
    )
    output_dir = tmp_path / 'runs' / request.run_id
    write_run_outputs(
        output_dir=output_dir,
        request=request,
        score_summary=score,
        changed_files=[ChangedFile(path='web/src/components/shell/AppShell.tsx', status='modified', added_lines=2, removed_lines=1)],
        validation_results=[ValidationResult(id='typecheck', command='pnpm --dir web typecheck', passed=True, exit_code=0, stdout='', stderr='')],
        workspace_path=tmp_path,
    )

    summaries = load_run_summaries(tmp_path / 'runs')
    aggregate_dir = write_aggregate_outputs(tmp_path / 'aggregate', summaries)

    assert (output_dir / 'summary.json').exists()
    assert (output_dir / 'report.md').exists()
    assert (aggregate_dir / 'comparison.json').exists()
    assert (aggregate_dir / 'comparison.csv').exists()
    comparison_markdown = (aggregate_dir / 'comparison.md').read_text()
    comparison_json = (aggregate_dir / 'comparison.json').read_text()
    assert '## Task Matrix' in comparison_markdown
    assert '## Rule Violations' in comparison_markdown
    assert 'Runtime rules' in comparison_markdown
    assert 'Final-result rules' in comparison_markdown
    assert '"task_comparisons"' in comparison_json


def test_reporting_rolls_up_violation_examples(tmp_path: Path) -> None:
    aggregate_dir = write_aggregate_outputs(
        tmp_path / 'aggregate',
        [
            {
                'run_id': 'task-one-condition_md',
                'task_id': 'task-one',
                'task_title': 'Task one',
                'condition': 'condition_md',
                'normalized_score': 0.5,
                'instruction_adherence_rate': 0.4,
                'hard_violation_count': 1,
                'task_success': False,
                'rules': [
                    {
                        'rule_id': '1_validate_before_conclude',
                        'title': 'Validate before conclude',
                        'verdict': 'fail',
                        'severity': 'hard',
                        'evidence': ['No validation ran after edits.'],
                    },
                    {
                        'rule_id': '2_minimal_change',
                        'title': 'Minimal change',
                        'verdict': 'partial',
                        'severity': 'soft',
                        'evidence': ['Changed one extra file.'],
                    },
                ],
            },
            {
                'run_id': 'task-one-condition_mcp',
                'task_id': 'task-one',
                'task_title': 'Task one',
                'condition': 'condition_mcp',
                'normalized_score': 0.9,
                'instruction_adherence_rate': 0.9,
                'hard_violation_count': 0,
                'task_success': True,
                'rules': [
                    {
                        'rule_id': '1_validate_before_conclude',
                        'title': 'Validate before conclude',
                        'verdict': 'pass',
                        'severity': 'hard',
                        'evidence': ['Validation ran.'],
                    }
                ],
            },
        ],
    )
    comparison_markdown = (aggregate_dir / 'comparison.md').read_text()
    assert 'Hard-rule failures:' in comparison_markdown
    assert 'Soft degradations:' in comparison_markdown
    assert 'No validation ran after edits.' in comparison_markdown
    assert '`task-one`' in comparison_markdown
