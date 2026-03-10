from __future__ import annotations

from pathlib import Path

from ..models import InstructionBundle, TaskSpec
from .base import AgentRunner


class MdConditionRunner(AgentRunner):
    def build_instruction_bundle(self, task: TaskSpec) -> InstructionBundle:
        instruction_dir = self.repo_root / "benchmark" / "instructions" / "condition_md"
        sources = [path.relative_to(self.repo_root).as_posix() for path in sorted(instruction_dir.glob("*.md"))]
        content = "\n\n".join((self.repo_root / source).read_text() for source in sources)
        return InstructionBundle(
            kind="markdown",
            sources=sources,
            payload={"content": content},
        )

    def execute(self, run_request, observer):
        raise NotImplementedError("MdConditionRunner is a delivery adapter and must be wrapped by an executor.")
