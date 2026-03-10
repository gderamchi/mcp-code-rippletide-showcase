from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import ChangedFile, RunRequest, ScoreSummary, ValidationResult


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def write_run_outputs(
    output_dir: Path,
    request: RunRequest,
    score_summary: ScoreSummary,
    changed_files: list[ChangedFile],
    validation_results: list[ValidationResult],
    workspace_path: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        'run_id': request.run_id,
        'task_id': request.task.task_id,
        'task_title': request.task.title,
        'condition': request.condition,
        'runner_kind': request.runner_kind,
        'workspace_path': str(workspace_path),
        'normalized_score': score_summary.normalized_score,
        'instruction_adherence_rate': score_summary.instruction_adherence_rate,
        'hard_violation_count': score_summary.hard_violation_count,
        'task_success': score_summary.task_success,
        'rules': [_jsonable(rule) for rule in score_summary.rules],
        'validations': [_jsonable(result) for result in validation_results],
        'changed_files': [_jsonable(item) for item in changed_files],
    }

    (output_dir / 'summary.json').write_text(json.dumps(summary, indent=2))
    (output_dir / 'changed_files.json').write_text(
        json.dumps([_jsonable(item) for item in changed_files], indent=2)
    )
    markdown_report = build_run_markdown(summary)
    (output_dir / 'report.md').write_text(markdown_report)
    (output_dir / 'report.html').write_text(build_run_html(markdown_report))
    return summary


def build_run_markdown(summary: dict[str, Any]) -> str:
    rule_lines = '\n'.join(
        f"- `{rule['rule_id']}` {rule['verdict']} ({rule['severity']}): {', '.join(rule['evidence'])}"
        for rule in summary['rules']
    )
    validation_lines = '\n'.join(
        f"- `{result['id']}`: {'pass' if result['passed'] else 'fail'}"
        for result in summary['validations']
    )
    changed_lines = '\n'.join(
        f"- `{item['path']}` ({item['status']}) +{item['added_lines']} / -{item['removed_lines']}"
        for item in summary['changed_files']
    )
    return f"""# Run Report: {summary['run_id']}

- Task: `{summary['task_id']}` - {summary['task_title']}
- Condition: `{summary['condition']}`
- Score: {summary['normalized_score']:.2%}
- Instruction adherence: {summary['instruction_adherence_rate']:.2%}
- Hard violations: {summary['hard_violation_count']}
- Task success: {summary['task_success']}

## Rules
{rule_lines}

## Validations
{validation_lines or '- none'}

## Changed Files
{changed_lines or '- none'}
"""


def build_run_html(markdown_report: str) -> str:
    escaped = markdown_report.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Northstar Ops Benchmark Report</title>
    <style>
      body {{ font-family: ui-sans-serif, system-ui, sans-serif; margin: 2rem auto; max-width: 960px; color: #1f2b20; }}
      pre {{ white-space: pre-wrap; background: #f7f1e5; padding: 1rem; border-radius: 12px; }}
    </style>
  </head>
  <body>
    <pre>{escaped}</pre>
  </body>
</html>
"""


def load_run_summaries(runs_dir: Path) -> list[dict[str, Any]]:
    return [
        json.loads(path.read_text())
        for path in sorted(runs_dir.glob('*/summary.json'))
    ]


def write_aggregate_outputs(root_dir: Path, summaries: list[dict[str, Any]]) -> Path:
    timestamp = datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')
    output_dir = root_dir / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    by_condition: dict[str, list[dict[str, Any]]] = {}
    for summary in summaries:
        by_condition.setdefault(summary['condition'], []).append(summary)

    comparison = {
        'conditions': {},
        'runs': summaries,
    }
    for condition, condition_runs in by_condition.items():
        rule_rates: dict[str, float] = {}
        for run in condition_runs:
            for rule in run['rules']:
                rule_rates.setdefault(rule['rule_id'], 0.0)
                if rule['verdict'] == 'pass':
                    rule_rates[rule['rule_id']] += 1.0
                elif rule['verdict'] == 'partial':
                    rule_rates[rule['rule_id']] += 0.5
        denominator = len(condition_runs) or 1
        comparison['conditions'][condition] = {
            'average_score': round(
                sum(run['normalized_score'] for run in condition_runs) / denominator,
                4,
            ),
            'average_instruction_adherence': round(
                sum(run['instruction_adherence_rate'] for run in condition_runs) / denominator,
                4,
            ),
            'hard_violation_count': sum(run['hard_violation_count'] for run in condition_runs),
            'task_success_rate': round(
                sum(1 for run in condition_runs if run['task_success']) / denominator,
                4,
            ),
            'rule_pass_rates': {
                rule_id: round(value / denominator, 4) for rule_id, value in rule_rates.items()
            },
        }

    (output_dir / 'comparison.json').write_text(json.dumps(comparison, indent=2))
    _write_comparison_csv(output_dir / 'comparison.csv', summaries)
    (output_dir / 'comparison.md').write_text(build_comparison_markdown(comparison))
    return output_dir


def _write_comparison_csv(csv_path: Path, summaries: list[dict[str, Any]]) -> None:
    with csv_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                'run_id',
                'task_id',
                'condition',
                'normalized_score',
                'instruction_adherence_rate',
                'hard_violation_count',
                'task_success',
            ],
        )
        writer.writeheader()
        for summary in summaries:
            writer.writerow(
                {
                    'run_id': summary['run_id'],
                    'task_id': summary['task_id'],
                    'condition': summary['condition'],
                    'normalized_score': summary['normalized_score'],
                    'instruction_adherence_rate': summary['instruction_adherence_rate'],
                    'hard_violation_count': summary['hard_violation_count'],
                    'task_success': summary['task_success'],
                }
            )


def build_comparison_markdown(comparison: dict[str, Any]) -> str:
    lines = ['# Northstar Ops Benchmark Comparison', '']
    for condition, payload in comparison['conditions'].items():
        lines.extend(
            [
                f"## {condition}",
                f"- Average score: {payload['average_score']:.2%}",
                f"- Instruction adherence: {payload['average_instruction_adherence']:.2%}",
                f"- Hard violations: {payload['hard_violation_count']}",
                f"- Task success rate: {payload['task_success_rate']:.2%}",
                '',
            ]
        )
    return '\n'.join(lines)

