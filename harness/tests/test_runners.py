import json
from pathlib import Path

from harness.logging import EventLogger
from harness.models import RunRequest, RunResult, TaskSpec, DiffLimits
from harness.observer import RunObserver
from harness.runners.external_process import ExternalProcessRunner


def _dummy_task() -> TaskSpec:
    return TaskSpec(
        task_id='dummy',
        title='Dummy task',
        prompt_file='benchmark/prompts/mobile_drawer_route_close.md',
        expected_files=['web/src/components/shell/AppShell.tsx'],
        allowed_files=['web/src/components/shell/AppShell.tsx'],
        forbidden_files=['protected/**'],
        required_validations=[],
        forbidden_commands=[],
        completion_checks=[],
        clarification_allowed=False,
        diff_limits=DiffLimits(max_files_changed=1, max_lines_changed=5),
    )


def test_external_runner_consumes_ndjson(tmp_path: Path) -> None:
    script_path = tmp_path / 'adapter.py'
    script_path.write_text(
        "\n".join(
            [
                'import json, sys',
                'request = json.load(open(sys.argv[1]))',
                "print(json.dumps({'event_type': 'agent_message', 'payload': {'content': 'adapter started'}}))",
                "print(json.dumps({'event_type': 'tool_call', 'payload': {'tool': 'apply_patch'}}))",
                "print(json.dumps({'event_type': 'run_finished', 'payload': {'status': 'completed', 'final_message': 'done'}}))",
            ]
        )
    )

    request = RunRequest(
        run_id='dummy-run',
        task=_dummy_task(),
        condition='condition_md',
        workspace_path=tmp_path,
        output_dir=tmp_path / 'output',
        instruction_payload={'prompt': 'dummy'},
        protected_globs=['protected/**'],
        canary_values=[],
        runner_kind='external',
        adapter_command=f'python3 {script_path} {{request_file}}',
    )
    logger = EventLogger(tmp_path / 'events.jsonl')
    observer = RunObserver('condition_md', logger, 'dummy-run', 'dummy', tmp_path)

    runner = ExternalProcessRunner()
    result: RunResult = runner.execute(request, observer)

    event_types = [event['event_type'] for event in logger.events]
    assert result.final_status == 'completed'
    assert 'tool_call' in event_types
    assert 'run_finished' in event_types

