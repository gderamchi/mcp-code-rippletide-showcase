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
        'task_comparisons': build_task_comparisons(summaries),
    }
    for condition, condition_runs in by_condition.items():
        rule_rates: dict[str, float] = {}
        violations = build_condition_violations(condition_runs)
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
            'violations': violations,
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
    lines.extend(['## Overview', ''])
    lines.extend(
        [
            '| Condition | Average score | Instruction adherence | Hard violations | Task success rate |',
            '| --- | ---: | ---: | ---: | ---: |',
        ]
    )
    for condition, payload in comparison['conditions'].items():
        lines.extend(
            [
                (
                    f"| `{condition}` | {payload['average_score']:.2%} | "
                    f"{payload['average_instruction_adherence']:.2%} | "
                    f"{payload['hard_violation_count']} | {payload['task_success_rate']:.2%} |"
                )
            ]
        )
    lines.append('')

    if comparison['task_comparisons']:
        lines.extend(['## Task Matrix', ''])
        lines.extend(
            [
                '| Task | MD score | MCP score | Delta (MCP-MD) | MD hard fails | MCP hard fails |',
                '| --- | ---: | ---: | ---: | ---: | ---: |',
            ]
        )
        for row in comparison['task_comparisons']:
            lines.append(
                (
                    f"| `{row['task_id']}` | {format_percent(row['condition_md_score'])} | "
                    f"{format_percent(row['condition_mcp_score'])} | {format_delta(row['score_delta'])} | "
                    f"{row['condition_md_hard_failures']} | {row['condition_mcp_hard_failures']} |"
                )
            )
        lines.append('')

    lines.extend(['## Rule Violations', ''])
    for condition, payload in comparison['conditions'].items():
        lines.extend([f"### {condition}", ''])
        hard_violations = payload['violations']['hard']
        soft_violations = payload['violations']['soft']
        if not hard_violations and not soft_violations:
            lines.extend(['- No rule degradations recorded.', ''])
            continue
        if hard_violations:
            lines.append('Hard-rule failures:')
            for violation in hard_violations:
                lines.append(
                    (
                        f"- `{violation['rule_id']}` {violation['title']}: "
                        f"{violation['fail_count']} fail, {violation['partial_count']} partial"
                    )
                )
                for example in violation['examples']:
                    lines.append(
                        f"  Example `{example['task_id']}` ({example['verdict']}): {example['evidence']}"
                    )
            lines.append('')
        if soft_violations:
            lines.append('Soft degradations:')
            for violation in soft_violations:
                lines.append(
                    (
                        f"- `{violation['rule_id']}` {violation['title']}: "
                        f"{violation['fail_count']} fail, {violation['partial_count']} partial"
                    )
                )
                for example in violation['examples']:
                    lines.append(
                        f"  Example `{example['task_id']}` ({example['verdict']}): {example['evidence']}"
                    )
            lines.append('')
    return '\n'.join(lines)


def build_task_comparisons(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_task: dict[str, dict[str, dict[str, Any]]] = {}
    for summary in summaries:
        by_task.setdefault(summary['task_id'], {})[summary['condition']] = summary

    comparisons: list[dict[str, Any]] = []
    for task_id in sorted(by_task):
        condition_map = by_task[task_id]
        md_summary = condition_map.get('condition_md')
        mcp_summary = condition_map.get('condition_mcp')
        md_score = md_summary['normalized_score'] if md_summary else None
        mcp_score = mcp_summary['normalized_score'] if mcp_summary else None
        score_delta = (
            round(mcp_score - md_score, 4)
            if md_score is not None and mcp_score is not None
            else None
        )
        comparisons.append(
            {
                'task_id': task_id,
                'task_title': (md_summary or mcp_summary)['task_title'],
                'condition_md_score': md_score,
                'condition_mcp_score': mcp_score,
                'score_delta': score_delta,
                'condition_md_hard_failures': count_hard_failures(md_summary),
                'condition_mcp_hard_failures': count_hard_failures(mcp_summary),
            }
        )
    return comparisons


def build_condition_violations(condition_runs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, dict[str, Any]] = {}
    for run in condition_runs:
        for rule in run['rules']:
            if rule['verdict'] not in {'fail', 'partial'}:
                continue
            entry = grouped.setdefault(
                rule['rule_id'],
                {
                    'rule_id': rule['rule_id'],
                    'title': rule['title'],
                    'severity': rule['severity'],
                    'fail_count': 0,
                    'partial_count': 0,
                    'examples': [],
                },
            )
            if rule['verdict'] == 'fail':
                entry['fail_count'] += 1
            else:
                entry['partial_count'] += 1
            if len(entry['examples']) < 3:
                entry['examples'].append(
                    {
                        'task_id': run['task_id'],
                        'verdict': rule['verdict'],
                        'evidence': summarize_evidence(rule['evidence']),
                    }
                )

    ordered = sorted(
        grouped.values(),
        key=lambda item: (item['severity'] != 'hard', -item['fail_count'], -item['partial_count'], item['rule_id']),
    )
    return {
        'hard': [item for item in ordered if item['severity'] == 'hard'],
        'soft': [item for item in ordered if item['severity'] == 'soft'],
    }


def summarize_evidence(evidence: list[str]) -> str:
    if not evidence:
        return 'No evidence recorded.'
    combined = ' | '.join(evidence[:2])
    return combined if len(combined) <= 220 else combined[:217] + '...'


def count_hard_failures(summary: dict[str, Any] | None) -> int:
    if not summary:
        return 0
    return sum(
        1
        for rule in summary['rules']
        if rule['severity'] == 'hard' and rule['verdict'] == 'fail'
    )


def format_percent(value: float | None) -> str:
    if value is None:
        return 'n/a'
    return f'{value:.2%}'


def format_delta(value: float | None) -> str:
    if value is None:
        return 'n/a'
    sign = '+' if value > 0 else ''
    return f'{sign}{value:.2%}'
