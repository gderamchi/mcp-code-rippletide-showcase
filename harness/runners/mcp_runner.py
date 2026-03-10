from __future__ import annotations

import json
from pathlib import Path

from ..task_loader import read_prompt
from ..models import RunRequest, TaskSpec
from .base import AgentRunner


class McpConditionRunner(AgentRunner):
    def prepare(
        self,
        output_dir: Path,
        run_id: str,
        task: TaskSpec,
        workspace_path: Path,
        runner_kind: str,
        adapter_command: str | None = None,
    ) -> RunRequest:
        manifest_path = self.repo_root / 'benchmark' / 'instructions' / 'condition_mcp' / 'context_manifest.json'
        provider_path = self.repo_root / 'benchmark' / 'instructions' / 'condition_mcp' / 'demo_provider.json'
        canary_values = (self.repo_root / 'protected' / 'canary.env').read_text().splitlines()
        return RunRequest(
            run_id=run_id,
            task=task,
            condition='condition_mcp',
            workspace_path=workspace_path,
            output_dir=output_dir,
            instruction_payload={
                'prompt': read_prompt(self.repo_root, task),
                'context_manifest': json.loads(manifest_path.read_text()),
                'provider': json.loads(provider_path.read_text()),
            },
            protected_globs=task.forbidden_files,
            canary_values=canary_values,
            runner_kind=runner_kind,
            adapter_command=adapter_command,
        )

