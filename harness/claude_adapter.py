from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, TextIO

from .adapter_common import (
    build_prompt,
    emit,
    emit_final_file_writes,
    emit_tool_command,
    emit_tool_result,
    extract_user_change_paths,
    load_request,
)


def build_claude_command(request: dict, mcp_config_path: Path | None = None) -> list[str]:
    command = [
        'claude',
        '-p',
        '--output-format',
        'stream-json',
        '--verbose',
        '--permission-mode',
        'bypassPermissions',
        '--add-dir',
        request['workspace_path'],
        '--tools',
        'default',
    ]

    if mcp_config_path is not None:
        command.extend(['--mcp-config', str(mcp_config_path), '--strict-mcp-config'])

    return command


def _flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        chunks: list[str] = []
        for item in value:
            if isinstance(item, dict) and item.get('type') == 'text' and item.get('text'):
                chunks.append(str(item['text']))
            elif isinstance(item, str):
                chunks.append(item)
        return '\n'.join(chunk for chunk in chunks if chunk)
    if isinstance(value, dict):
        if value.get('text'):
            return str(value['text'])
        if value.get('content'):
            return _flatten_text(value['content'])
    return ''


def _tool_name(block: dict[str, Any]) -> str:
    return str(block.get('name') or block.get('tool_name') or '').lower()


def _tool_command_from_input(block: dict[str, Any]) -> str | None:
    input_payload = block.get('input')
    if not isinstance(input_payload, dict):
        return None
    for key in ('command', 'cmd'):
        value = input_payload.get(key)
        if value:
            return str(value)
    return None


def _extract_file_path(block: dict[str, Any]) -> str | None:
    input_payload = block.get('input')
    if not isinstance(input_payload, dict):
        return None
    for key in ('file_path', 'path', 'target_file'):
        value = input_payload.get(key)
        if value:
            return str(value)
    return None


def translate_claude_stream(
    process: subprocess.Popen[str],
    workspace_path: Path,
    request: dict,
    stream: TextIO,
) -> tuple[str, bool, str]:
    del request
    pending_shell_commands: dict[str, str] = {}
    last_agent_message = ''
    saw_turn_completed = False

    assert process.stdout is not None
    for raw_line in process.stdout:
        line = raw_line.strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue

        message_type = payload.get('type')
        if message_type == 'result':
            saw_turn_completed = payload.get('subtype') != 'error'
            result_text = payload.get('result')
            if isinstance(result_text, str) and result_text:
                last_agent_message = result_text
            continue
        if message_type in {'system', 'error'}:
            continue

        message = payload.get('message') if isinstance(payload.get('message'), dict) else payload
        role = message.get('role') or message_type
        content_blocks = message.get('content')
        if not isinstance(content_blocks, list):
            text = _flatten_text(message.get('text') or message.get('content') or '')
            if text and role == 'assistant':
                last_agent_message = text
                emit('agent_message', {'role': 'assistant', 'content': text}, stream)
            continue

        for block in content_blocks:
            if not isinstance(block, dict):
                continue
            block_type = block.get('type')

            if block_type == 'text' and role == 'assistant':
                text = _flatten_text(block)
                if text:
                    last_agent_message = text
                    emit('agent_message', {'role': 'assistant', 'content': text}, stream)
                continue

            if block_type in {'tool_use', 'mcp_tool_use'} and role == 'assistant':
                tool_name = _tool_name(block)
                tool_use_id = str(block.get('id') or block.get('tool_use_id') or '')
                if tool_name.startswith('bash'):
                    command = _tool_command_from_input(block)
                    if command:
                        if tool_use_id:
                            pending_shell_commands[tool_use_id] = command
                        emit_tool_command(command, workspace_path, stream)
                elif tool_name.startswith(('read', 'edit', 'write', 'multiedit', 'notebookedit')):
                    file_path = _extract_file_path(block)
                    if file_path:
                        event_type = 'file_read' if tool_name.startswith('read') else 'file_write'
                        emit(event_type, {'path': file_path}, stream)
                    emit('tool_call', {'tool': block.get('name') or block.get('tool_name')}, stream)
                else:
                    emit(
                        'tool_call',
                        {'tool': block.get('name') or block.get('tool_name'), 'input': block.get('input')},
                        stream,
                    )
                continue

            if block_type in {'tool_result', 'mcp_tool_result'}:
                tool_use_id = str(block.get('tool_use_id') or '')
                stdout = _flatten_text(block.get('content'))
                command = pending_shell_commands.pop(tool_use_id, '')
                if command:
                    emit_tool_result(
                        command,
                        status='failed' if block.get('is_error') else 'completed',
                        exit_code=1 if block.get('is_error') else 0,
                        stdout=stdout,
                        stderr='',
                        stream=stream,
                    )
                else:
                    emit(
                        'tool_result',
                        {
                            'tool': 'mcp' if block_type == 'mcp_tool_result' else 'tool',
                            'tool_use_id': tool_use_id,
                            'status': 'failed' if block.get('is_error') else 'completed',
                            'content': stdout,
                        },
                        stream,
                    )

    stderr_output = ''
    if process.stderr is not None:
        stderr_output = process.stderr.read()

    return last_agent_message, saw_turn_completed, stderr_output


def run_adapter(request_path: Path, stream: TextIO = sys.stdout) -> int:
    request = load_request(request_path)
    workspace_path = Path(request['workspace_path'])
    seed_user_change_paths = extract_user_change_paths(request, request_path)

    mcp_config_path = None
    server_config = request['instruction_payload'].get('mcp_server_config')
    if isinstance(server_config, dict) and server_config:
        mcp_config_path = request_path.parent / 'claude_mcp_config.json'
        mcp_config_path.write_text(json.dumps(server_config, indent=2))

    prompt = build_prompt(request)
    claude_command = build_claude_command(request, mcp_config_path)
    process = subprocess.Popen(
        claude_command,
        cwd=workspace_path,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdin is not None
    process.stdin.write(prompt)
    process.stdin.close()

    final_message, saw_turn_completed, stderr_output = translate_claude_stream(
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
            'final_message': final_message or 'Claude Code run completed.',
            'adapter': 'claude',
            'stderr': stderr_output,
        },
        stream,
    )
    return return_code
