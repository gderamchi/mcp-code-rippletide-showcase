from __future__ import annotations

from ..models import InstructionBundle, TaskSpec
from .base import AgentRunner


class McpConditionRunner(AgentRunner):
    def build_instruction_bundle(self, task: TaskSpec) -> InstructionBundle:
        source = "benchmark/instructions/condition_mcp/context_manifest.json"
        payload = (self.repo_root / source).read_text()
        return InstructionBundle(
            kind="mcp",
            sources=[source],
            payload={"manifest": payload},
        )

    def execute(self, run_request, observer):
        raise NotImplementedError("McpConditionRunner is a delivery adapter and must be wrapped by an executor.")
