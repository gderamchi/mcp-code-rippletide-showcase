from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from ..models import ConditionBundle, RunRequest, TaskSpec
from .base import AgentExecutor, AgentRunner


def _load_markdown_bundle(instructions_dir: Path) -> ConditionBundle:
    items = []
    for path in sorted(instructions_dir.glob("*.md")):
        items.append(
            {
                "path": path.relative_to(instructions_dir.parent.parent).as_posix(),
                "title": path.stem,
                "content": path.read_text(encoding="utf-8"),
            }
        )
    return ConditionBundle(bundle_type="markdown", items=items)


def _load_mcp_bundle(instructions_dir: Path) -> ConditionBundle:
    items = []
    for path in sorted(instructions_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        items.extend(payload["items"])
    return ConditionBundle(bundle_type="mcp", items=items)


class MdConditionRunner(AgentRunner):
    def __init__(self, executor: AgentExecutor, instructions_dir: Path) -> None:
        super().__init__(condition="condition_md", executor=executor)
        self.instructions_dir = instructions_dir

    def prepare(self, repo_root: Path, task: TaskSpec, workspace: Path, protected_paths: list[str]) -> RunRequest:
        prompt = (repo_root / task.prompt_file).read_text(encoding="utf-8")
        bundle = _load_markdown_bundle(self.instructions_dir)
        return RunRequest(
            run_id=str(uuid4()),
            condition=self.condition,
            task=task,
            workspace=workspace,
            prompt=prompt,
            instructions=bundle,
            protected_paths=protected_paths,
        )


class McpConditionRunner(AgentRunner):
    def __init__(self, executor: AgentExecutor, instructions_dir: Path) -> None:
        super().__init__(condition="condition_mcp", executor=executor)
        self.instructions_dir = instructions_dir

    def prepare(self, repo_root: Path, task: TaskSpec, workspace: Path, protected_paths: list[str]) -> RunRequest:
        prompt = (repo_root / task.prompt_file).read_text(encoding="utf-8")
        bundle = _load_mcp_bundle(self.instructions_dir)
        return RunRequest(
            run_id=str(uuid4()),
            condition=self.condition,
            task=task,
            workspace=workspace,
            prompt=prompt,
            instructions=bundle,
            protected_paths=protected_paths,
        )
