from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import TextIO


READ_COMMAND_HINTS = ('cat ', 'sed ', 'rg ', 'grep ', 'find ', 'ls ', 'node -p')
WRITE_COMMAND_HINTS = ('apply_patch', 'cat >', 'tee ', 'sed -i', 'perl -0pi', 'mv ', 'cp ')
FILE_PATTERN = re.compile(
    r'(?<![\w/.-])(?:\.\/)?(?:[A-Za-z0-9_.-]+/)*'
    r'(?:[A-Za-z0-9_.-]+\.(?:ts|tsx|js|jsx|json|md|css|toml|env|yaml|yml|txt)|'
    r'package\.json|README\.md|AGENTS\.md)(?![\w/.-])'
)


def load_request(request_path: Path) -> dict:
    return json.loads(request_path.read_text())


def build_prompt(request: dict) -> str:
    task_prompt = request['instruction_payload']['prompt'].strip()
    benchmark_wrapper = (
        'Benchmark wrapper:\n'
        '- Treat the supplied condition context as external instructions that may be stale or partially mismatched.\n'
        '- Inspect the actual repository before acting, and prefer observed repo structure over conflicting assumptions.\n'
        '- Stay focused on the benchmark task only; do not apply unrelated documentation or repo-maintenance rules unless the task requires them.\n'
        '- Validate the smallest relevant change before concluding.\n'
    )
    if request['condition'] == 'condition_md':
        instruction_bundle = request['instruction_payload']['instruction_bundle']
        markdown_rules = '\n\n'.join(item['content'].strip() for item in instruction_bundle)
        return (
            'You are running in the markdown-only benchmark condition.\n'
            'Use the provided repository instruction bundle as your authoritative project context.\n\n'
            f'{benchmark_wrapper}\n'
            f'{markdown_rules}\n\n'
            'Task:\n'
            f'{task_prompt}\n'
        )

    mcp_bundle = request['instruction_payload']['mcp_json_bundle']
    bundle_paths = ', '.join(item['path'] for item in mcp_bundle)
    return (
        'You are running in the MCP benchmark condition.\n'
        'Use the configured MCP server for repository context instead of relying on an injected markdown ruleset.\n'
        f'The active MCP bundle for this run is described by: {bundle_paths}\n\n'
        f'{benchmark_wrapper}\n'
        'Task:\n'
        f'{task_prompt}\n'
    )


def _format_config_key(prefix: str, key: str, field: str) -> str:
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
        return f'{prefix}.{key}.{field}'
    return f'{prefix}."{key}".{field}'


def build_codex_command(request: dict) -> list[str]:
    workspace_path = request['workspace_path']
    command = [
        'codex',
        'exec',
        '--json',
        '--ephemeral',
        '--sandbox',
        'workspace-write',
        '-C',
        workspace_path,
        '-c',
        'features.multi_agent=false',
        '-c',
        'features.child_agents_md=false',
        '-c',
        'features.memory_tool=false',
        '-c',
        'features.apps_mcp_gateway=false',
        '-c',
        'features.sqlite=false',
        '-c',
        'suppress_unstable_features_warning=true',
        '-c',
        'mcp_servers={}',
    ]

    if request['condition'] == 'condition_mcp':
        server_config = request['instruction_payload'].get('mcp_server_config') or {}
        for server_name, server_definition in server_config.get('mcpServers', {}).items():
            url = server_definition.get('url')
            bearer_token_env_var = server_definition.get('bearerTokenEnvVar')
            if url:
                command.extend(
                    ['-c', f'{_format_config_key("mcp_servers", server_name, "url")}="{url}"']
                )
                command.extend(
                    ['-c', f'{_format_config_key("mcp_servers", server_name, "enabled")}=true']
                )
            if bearer_token_env_var:
                command.extend(
                    [
                        '-c',
                        (
                            f'{_format_config_key("mcp_servers", server_name, "bearer_token_env_var")}'
                            f'="{bearer_token_env_var}"'
                        ),
                    ]
                )

    command.append('-')
    return command


def _unwrap_shell_command(command: str) -> str:
    parts = shlex.split(command)
    if '-lc' in parts:
        shell_index = parts.index('-lc')
        if shell_index + 1 < len(parts):
            return parts[shell_index + 1]
    return command


def _extract_paths_from_command(command: str, workspace_path: Path) -> list[str]:
    shell_command = _unwrap_shell_command(command)
    matches = []
    for raw_match in FILE_PATTERN.findall(shell_command):
        cleaned = raw_match.removeprefix('./')
        candidate = workspace_path / cleaned
        if candidate.exists():
            matches.append(cleaned)
    return sorted(set(matches))


def extract_user_change_paths(request: dict, request_path: Path) -> set[str]:
    seed_patch = request['task'].get('seed_user_changes_patch')
    if not seed_patch:
        return set()

    patch_path = Path(request['workspace_path']) / seed_patch
    if not patch_path.exists():
        return set()

    paths: set[str] = set()
    for line in patch_path.read_text().splitlines():
        if line.startswith('+++ b/'):
            paths.add(line.replace('+++ b/', '', 1))
    return paths


def emit(event_type: str, payload: dict, stream: TextIO) -> None:
    stream.write(json.dumps({'event_type': event_type, 'payload': payload}) + '\n')
    stream.flush()


def _emit_file_events(command: str, workspace_path: Path, stream: TextIO) -> None:
    path_matches = _extract_paths_from_command(command, workspace_path)
    shell_command = _unwrap_shell_command(command)
    if any(hint in shell_command for hint in READ_COMMAND_HINTS):
        for relative_path in path_matches:
            emit('file_read', {'path': relative_path}, stream)
    if any(hint in shell_command for hint in WRITE_COMMAND_HINTS):
        for relative_path in path_matches:
            emit('file_write', {'path': relative_path}, stream)


def translate_codex_stream(
    process: subprocess.Popen[str],
    workspace_path: Path,
    request: dict,
    stream: TextIO,
) -> tuple[str, bool, str]:
    last_agent_message = ''
    saw_turn_completed = False

    assert process.stdout is not None
    for line in process.stdout:
        line = line.strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = payload.get('type')
        if event_type == 'turn.completed':
            saw_turn_completed = True
            continue
        if event_type in {'thread.started', 'turn.started'}:
            continue
        if event_type != 'item.started' and event_type != 'item.completed':
            continue

        item = payload.get('item', {})
        item_type = item.get('type')
        is_started = event_type == 'item.started'

        if item_type == 'error':
            continue

        if item_type in {'agent_message', 'reasoning'} and not is_started:
            text = item.get('text', '')
            if text:
                last_agent_message = text
                emit(
                    'agent_message',
                    {'role': 'assistant' if item_type == 'agent_message' else 'reasoning', 'content': text},
                    stream,
                )
            continue

        if item_type == 'command_execution':
            command = item.get('command', '')
            if is_started:
                emit('tool_call', {'tool': 'shell', 'command': command}, stream)
                emit('shell_command', {'command': command, 'cwd': '.'}, stream)
                _emit_file_events(command, workspace_path, stream)
            else:
                emit(
                    'shell_output',
                    {
                        'command': command,
                        'exit_code': item.get('exit_code'),
                        'stdout': item.get('aggregated_output', ''),
                        'stderr': '',
                    },
                    stream,
                )
                emit(
                    'tool_result',
                    {
                        'tool': 'shell',
                        'command': command,
                        'status': item.get('status'),
                        'exit_code': item.get('exit_code'),
                    },
                    stream,
                )
            continue

        if item_type == 'collab_tool_call':
            tool_payload = {
                'tool': item.get('tool'),
                'status': item.get('status'),
                'prompt': item.get('prompt'),
                'receiver_thread_ids': item.get('receiver_thread_ids', []),
            }
            emit('tool_call' if is_started else 'tool_result', tool_payload, stream)

    stderr_output = ''
    if process.stderr is not None:
        stderr_output = process.stderr.read()

    return last_agent_message, saw_turn_completed, stderr_output


def emit_final_file_writes(
    workspace_path: Path,
    seed_user_change_paths: set[str],
    stream: TextIO,
) -> None:
    diff = subprocess.run(
        ['git', 'diff', '--name-only'],
        cwd=workspace_path,
        text=True,
        capture_output=True,
        check=False,
    )
    for relative_path in sorted(
        path
        for path in diff.stdout.splitlines()
        if path and path not in seed_user_change_paths
    ):
        emit('file_write', {'path': relative_path}, stream)


def run_adapter(request_path: Path, stream: TextIO = sys.stdout) -> int:
    request = load_request(request_path)
    workspace_path = Path(request['workspace_path'])
    seed_user_change_paths = extract_user_change_paths(request, request_path)

    codex_command = build_codex_command(request)
    prompt = build_prompt(request)
    process = subprocess.Popen(
        codex_command,
        cwd=workspace_path,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdin is not None
    process.stdin.write(prompt)
    process.stdin.close()

    final_message, saw_turn_completed, stderr_output = translate_codex_stream(
        process,
        workspace_path,
        request,
        stream,
    )
    return_code = process.wait()
    emit_final_file_writes(workspace_path, seed_user_change_paths, stream)
    emit(
        'run_finished',
        {
            'status': 'completed' if return_code == 0 and saw_turn_completed else 'failed',
            'final_message': final_message or 'Codex run completed.',
            'adapter': 'codex',
            'stderr': stderr_output,
        },
        stream,
    )
    return return_code
