from __future__ import annotations

from pathlib import Path

from harness.agent_registry import list_agent_backends, resolve_external_adapter_command


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_resolve_external_adapter_command_supports_codex_claude_and_custom() -> None:
    codex_command = resolve_external_adapter_command(
        benchmark_root=REPO_ROOT,
        agent_backend='codex',
        adapter_command=None,
    )
    claude_command = resolve_external_adapter_command(
        benchmark_root=REPO_ROOT,
        agent_backend='claude',
        adapter_command=None,
    )
    custom_command = resolve_external_adapter_command(
        benchmark_root=REPO_ROOT,
        agent_backend='custom',
        adapter_command='python3 adapter.py {request_file}',
    )

    assert codex_command.endswith('scripts/adapter_codex.py {request_file}')
    assert claude_command.endswith('scripts/adapter_claude.py {request_file}')
    assert custom_command == 'python3 adapter.py {request_file}'


def test_list_agent_backends_marks_codex_as_default_external_backend() -> None:
    backends = list_agent_backends(REPO_ROOT)
    backend_keys = {backend.key for backend in backends}

    assert {'codex', 'claude', 'custom'} <= backend_keys
    assert any(backend.key == 'codex' and backend.default_for_external for backend in backends)
    assert any(backend.key == 'custom' and backend.requires_custom_command for backend in backends)
