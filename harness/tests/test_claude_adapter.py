from __future__ import annotations

import io
import json
from pathlib import Path

from harness.claude_adapter import build_claude_command, translate_claude_stream


REPO_ROOT = Path(__file__).resolve().parents[2]


def make_request() -> dict:
    return {
        'condition': 'condition_mcp',
        'workspace_path': str(REPO_ROOT),
        'task': {'seed_user_changes_patch': None},
        'instruction_payload': {
            'prompt': 'Fix the task.',
            'mcp_json_bundle': [
                {
                    'path': 'benchmark/instructions/condition_mcp/context.json',
                    'content': {'condition': 'condition_mcp'},
                }
            ],
            'mcp_server_config': {
                'mcpServers': {
                    'rippletide': {
                        'type': 'http',
                        'url': 'https://mcp.example.test',
                    }
                }
            },
        },
    }


class FakeProcess:
    def __init__(self, stdout_lines: list[str], stderr_text: str = '') -> None:
        self.stdout = io.StringIO('\n'.join(stdout_lines) + '\n')
        self.stderr = io.StringIO(stderr_text)


def test_build_claude_command_includes_mcp_config() -> None:
    command = build_claude_command(make_request(), REPO_ROOT / 'mcp.json')
    joined = ' '.join(command)

    assert '--output-format stream-json' in joined
    assert '--permission-mode bypassPermissions' in joined
    assert '--mcp-config' in command
    assert '--strict-mcp-config' in command


def test_translate_claude_stream_maps_tool_use_and_result() -> None:
    stream = io.StringIO()
    process = FakeProcess(
        [
            json.dumps({'type': 'system', 'subtype': 'init'}),
            json.dumps(
                {
                    'type': 'assistant',
                    'message': {
                        'role': 'assistant',
                        'content': [
                            {'type': 'text', 'text': 'Inspecting the repo.'},
                            {
                                'type': 'tool_use',
                                'id': 'tool_1',
                                'name': 'Bash',
                                'input': {'command': 'cat package.json'},
                            },
                        ],
                    },
                }
            ),
            json.dumps(
                {
                    'type': 'user',
                    'message': {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'tool_result',
                                'tool_use_id': 'tool_1',
                                'content': [{'type': 'text', 'text': '{}'}],
                            }
                        ],
                    },
                }
            ),
            json.dumps({'type': 'result', 'subtype': 'success', 'result': 'Done'}),
        ]
    )

    final_message, saw_turn_completed, stderr_output = translate_claude_stream(
        process,
        REPO_ROOT,
        make_request(),
        stream,
    )
    events = [json.loads(line) for line in stream.getvalue().splitlines()]

    assert saw_turn_completed is True
    assert final_message == 'Done'
    assert stderr_output == ''
    assert any(event['event_type'] == 'agent_message' for event in events)
    assert any(event['event_type'] == 'shell_command' for event in events)
    assert any(event['event_type'] == 'file_read' for event in events)
    assert any(event['event_type'] == 'shell_output' for event in events)
