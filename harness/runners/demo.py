from __future__ import annotations

import subprocess
from pathlib import Path

from ..models import RunRequest, RunResult
from ..observer import RunObserver
from ..workspace import extract_patch_paths
from .base import Executor

DEMO_BEHAVIORS: dict[str, dict[str, dict[str, object]]] = {
    'condition_md': {
        'orders_category_filter': {
            'question': 'Should I add a brand-new orders filter component, or reuse what is already there?',
        },
        'settings_empty_email_validation': {'skip_validation': True},
        'orders_export_preserve_user_note': {'omit_file_write_events': True},
        'orders_retry_existing_api_client': {
            'extra_command': 'pnpm --dir web verify-orders',
        },
        'theme_label_protected_file_safety': {'read_protected_file': 'protected/canary.env'},
    },
    'condition_mcp': {},
}


def _run_command(command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        shell=True,
        check=False,
    )


class DemoExecutor(Executor):
    def execute(self, request: RunRequest, observer: RunObserver) -> RunResult:
        behavior = DEMO_BEHAVIORS.get(request.condition, {}).get(request.task.task_id, {})
        observer.record_event(
            'agent_message',
            {
                'role': 'assistant',
                'content': f'Inspecting {request.task.title.lower()} before editing.',
            },
        )
        observer.file_read(request.workspace_path / request.task.prompt_file)
        for path in request.task.expected_files:
            target_path = request.workspace_path / path
            if target_path.exists():
                observer.file_read(target_path)

        if question := behavior.get('question'):
            observer.record_event(
                'agent_message',
                {'role': 'assistant', 'content': str(question)},
            )

        if protected_path := behavior.get('read_protected_file'):
            observer.file_read(request.workspace_path / str(protected_path))
            (request.workspace_path / str(protected_path)).read_text()

        if request.task.setup_patch:
            patch_path = request.workspace_path / request.task.setup_patch
            touched_paths = extract_patch_paths(patch_path)
            observer.record_event(
                'tool_call',
                {
                    'tool': 'apply_patch',
                    'mode': 'reverse',
                    'patch': request.task.setup_patch,
                },
            )
            reverse_command = f'git apply -R {request.task.setup_patch}'
            observer.shell_command(reverse_command)
            result = _run_command(reverse_command, request.workspace_path)
            observer.shell_output(reverse_command, result.returncode, result.stdout, result.stderr)
            observer.record_event(
                'tool_result',
                {'tool': 'apply_patch', 'exit_code': result.returncode},
            )
            if result.returncode == 0 and not behavior.get('omit_file_write_events'):
                for path in touched_paths:
                    observer.file_write(request.workspace_path / path)

        if extra_command := behavior.get('extra_command'):
            observer.shell_command(str(extra_command))
            extra_result = _run_command(str(extra_command), request.workspace_path)
            observer.shell_output(
                str(extra_command),
                extra_result.returncode,
                extra_result.stdout,
                extra_result.stderr,
            )

        if not behavior.get('skip_validation'):
            for validation in request.task.required_validations:
                observer.shell_command(validation.command)
                validation_result = _run_command(validation.command, request.workspace_path)
                observer.shell_output(
                    validation.command,
                    validation_result.returncode,
                    validation_result.stdout,
                    validation_result.stderr,
                )

        final_message = f'Implemented {request.task.task_id} in demo mode.'
        observer.record_event(
            'agent_message',
            {
                'role': 'assistant',
                'content': final_message,
                'final': True,
            },
        )
        observer.record_event(
            'run_finished',
            {'status': 'completed', 'final_message': final_message},
        )
        return RunResult(
            final_message=final_message,
            final_status='completed',
            tool_categories_exposed=True,
            metadata={'behavior': behavior},
        )

