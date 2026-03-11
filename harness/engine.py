from __future__ import annotations

import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from .logging import EventLogger
from .models import RunRequest, RunResult, ScoringContext, TaskSpec, ValidationResult
from .observer import RunObserver
from .reporting import write_run_outputs
from .runners import DemoExecutor, ExternalProcessRunner
from .scoring import ScoringEngine, load_allowed_scripts, load_rulebook
from .task_loader import load_policy
from .workspace import (
    build_changed_files,
    create_workspace,
    diff_snapshot,
    git_status_snapshot,
    snapshot_tree,
)

RunStatusCallback = Callable[[str, dict], None]


def run_validations(workspace_root: Path, task: TaskSpec, observer: RunObserver) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for validation in task.required_validations:
        command = validation.command
        completed = subprocess.run(
            command,
            cwd=workspace_root,
            text=True,
            capture_output=True,
            shell=True,
            check=False,
        )
        result = ValidationResult(
            id=validation.id,
            command=command,
            passed=completed.returncode == 0,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        observer.record_event(
            'validation_result',
            {
                'id': validation.id,
                'command': command,
                'passed': result.passed,
                'exit_code': result.exit_code,
            },
        )
        results.append(result)
    return results


def build_executor(runner_kind: str):
    if runner_kind == 'demo':
        return DemoExecutor()
    return ExternalProcessRunner()


def execute_task_run(
    *,
    benchmark_root: Path,
    source_root: Path,
    task: TaskSpec,
    condition: str,
    instruction_payload: dict,
    runner_kind: str,
    output_dir: Path,
    adapter_command: str | None = None,
    protected_globs: list[str] | None = None,
    allowed_scripts: set[str] | None = None,
) -> dict:
    policy = load_policy(benchmark_root)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = f'{task.task_id}-{condition}'
    workspace = create_workspace(source_root, task)
    logger = EventLogger(output_dir / 'events.jsonl')
    observer = RunObserver(condition, logger, run_id, task.task_id, workspace.root)
    observer.record_event(
        'run_started',
        {'runner_kind': runner_kind, 'workspace_path': str(workspace.root)},
    )
    observer.record_event(
        'git_status_snapshot',
        {'stage': 'task_start', 'status': git_status_snapshot(workspace.root)},
    )

    request = RunRequest(
        run_id=run_id,
        task=task,
        condition=condition,
        workspace_path=workspace.root,
        output_dir=output_dir,
        instruction_payload=instruction_payload,
        protected_globs=protected_globs or task.forbidden_files,
        canary_values=(benchmark_root / 'protected' / 'canary.env').read_text().splitlines(),
        runner_kind=runner_kind,
        adapter_command=adapter_command,
    )
    observer.record_event(
        'instruction_injected',
        {
            'condition': condition,
            'prompt_file': task.prompt_file,
            'payload_keys': list(request.instruction_payload.keys()),
        },
    )
    executor = build_executor(runner_kind)
    run_result: RunResult = executor.execute(request, observer)
    observer.record_event(
        'git_status_snapshot',
        {'stage': 'after_agent', 'status': git_status_snapshot(workspace.root)},
    )
    observer.record_event(
        'diff_snapshot',
        {'stage': 'after_agent', 'diff_stat': diff_snapshot(workspace.root)},
    )

    validation_results = run_validations(workspace.root, task, observer)
    final_snapshot = snapshot_tree(workspace.root)
    changed_files = build_changed_files(workspace.task_start_snapshot, final_snapshot)
    scoring_context = ScoringContext(
        repo_root=workspace.root,
        run_request=request,
        run_result=run_result,
        events=logger.events,
        start_snapshot=workspace.task_start_snapshot,
        final_snapshot=final_snapshot,
        changed_files=changed_files,
        validation_results=validation_results,
        protected_globs=sorted(set(policy['protected_globs'] + request.protected_globs)),
        destructive_commands=policy['destructive_commands'],
        high_impact_patterns=policy['high_impact_command_patterns'],
        allowed_scripts=allowed_scripts if allowed_scripts is not None else load_allowed_scripts(source_root),
        user_change_paths=workspace.user_change_paths,
        canary_values=request.canary_values,
    )
    scoring_engine = ScoringEngine(policy, load_rulebook(benchmark_root))
    score_summary = scoring_engine.score(scoring_context)
    observer.record_event(
        'scoring_result',
        {
            'normalized_score': score_summary.normalized_score,
            'hard_violation_count': score_summary.hard_violation_count,
            'task_success': score_summary.task_success,
        },
    )
    return write_run_outputs(
        output_dir=output_dir,
        request=request,
        score_summary=score_summary,
        changed_files=changed_files,
        validation_results=validation_results,
        workspace_path=workspace.root,
    )


def execute_task_matrix(
    *,
    benchmark_root: Path,
    source_root: Path,
    run_items: list[dict],
    max_workers: int = 4,
    on_status: RunStatusCallback | None = None,
) -> list[dict]:
    summaries: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for run_item in run_items:
            if on_status is not None:
                on_status(
                    'task_scheduled',
                    {
                        'task_id': run_item['task'].task_id,
                        'condition': run_item['condition'],
                    },
                )
            futures.append(
                executor.submit(
                    execute_task_run,
                    benchmark_root=benchmark_root,
                    source_root=source_root,
                    task=run_item['task'],
                    condition=run_item['condition'],
                    instruction_payload=run_item['instruction_payload'],
                    runner_kind=run_item['runner_kind'],
                    output_dir=run_item['output_dir'],
                    adapter_command=run_item.get('adapter_command'),
                    protected_globs=run_item.get('protected_globs'),
                    allowed_scripts=run_item.get('allowed_scripts'),
                )
            )

        for future in as_completed(futures):
            summary = future.result()
            summaries.append(summary)
            if on_status is not None:
                on_status(
                    'task_completed',
                    {
                        'task_id': summary['task_id'],
                        'condition': summary['condition'],
                        'normalized_score': summary['normalized_score'],
                        'task_success': summary['task_success'],
                    },
                )

    return sorted(summaries, key=lambda item: item['run_id'])
