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
        bundle_dir = self.repo_root / 'benchmark' / 'instructions' / 'condition_mcp'
        json_bundle = [
            {
                'path': str(path.relative_to(self.repo_root)),
                'content': json.loads(path.read_text()),
            }
            for path in sorted(bundle_dir.glob('*.json'))
        ]
        mcp_server_config = self._merge_mcp_server_configs(json_bundle)
        canary_values = (self.repo_root / 'protected' / 'canary.env').read_text().splitlines()
        return RunRequest(
            run_id=run_id,
            task=task,
            condition='condition_mcp',
            workspace_path=workspace_path,
            output_dir=output_dir,
            instruction_payload={
                'prompt': read_prompt(self.repo_root, task),
                'mcp_json_bundle': json_bundle,
                'mcp_server_config': mcp_server_config,
            },
            protected_globs=task.forbidden_files,
            canary_values=canary_values,
            runner_kind=runner_kind,
            adapter_command=adapter_command,
        )

    @staticmethod
    def _merge_mcp_server_configs(json_bundle: list[dict]) -> dict | None:
        merged_servers: dict = {}
        for item in json_bundle:
            content = item.get('content')
            if not isinstance(content, dict):
                continue
            mcp_servers = content.get('mcpServers')
            if isinstance(mcp_servers, dict):
                merged_servers.update(mcp_servers)

        if not merged_servers:
            return None
        return {'mcpServers': merged_servers}
