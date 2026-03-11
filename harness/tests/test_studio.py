import json
from pathlib import Path

from harness.studio import build_dynamic_bundle, probe_repo_capabilities
from harness.studio_models import CompiledInstructions, PromptSource
from harness.alignment import McpManifestCompiler


def _create_pytest_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / 'sample-repo'
    repo_root.mkdir()
    (repo_root / 'pyproject.toml').write_text(
        '[project]\nname = "sample-repo"\nversion = "0.1.0"\n\n'
        '[tool.pytest.ini_options]\npythonpath = ["."]\n'
    )
    return repo_root


def test_probe_repo_capabilities_detects_pytest(tmp_path: Path) -> None:
    repo_root = _create_pytest_repo(tmp_path)

    capabilities = probe_repo_capabilities(repo_root)

    assert capabilities.supported is True
    assert capabilities.test_runner == 'pytest'
    assert capabilities.validation_command_template is not None


def test_build_dynamic_bundle_generates_runnable_mutation_tasks(tmp_path: Path) -> None:
    repo_root = _create_pytest_repo(tmp_path)
    bundle_root = tmp_path / 'bundle'
    compiled = CompiledInstructions(
        sources=[PromptSource(path='AGENTS.md', content='Validate before concluding.', source_kind='agents')],
        rules=[],
    )
    manifest = McpManifestCompiler().compile({'mcpServers': {}})
    capabilities = probe_repo_capabilities(repo_root)

    bundle = build_dynamic_bundle(
        bundle_root=bundle_root,
        source_root=repo_root,
        inputs={'repo_path': str(repo_root)},
        compiled_instructions=compiled,
        mcp_manifest=manifest,
        alignment_issues=[],
        capabilities=capabilities,
    )

    runnable_tasks = [item for item in bundle.generated_tasks if item.task is not None]
    assert runnable_tasks
    assert (bundle_root / 'generated_tasks.json').exists()
    payload = json.loads((bundle_root / 'generated_tasks.json').read_text())
    assert any(item['origin'] == 'mutation' for item in payload)
