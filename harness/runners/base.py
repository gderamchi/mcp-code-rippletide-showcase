from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import RunRequest, RunResult, TaskSpec
from ..observer import RunObserver


class Executor(ABC):
    @abstractmethod
    def execute(self, request: RunRequest, observer: RunObserver) -> RunResult:
        raise NotImplementedError


class AgentRunner(ABC):
    def __init__(self, repo_root: Path, executor: Executor) -> None:
        self.repo_root = repo_root
        self.executor = executor

    @abstractmethod
    def prepare(
        self,
        output_dir: Path,
        run_id: str,
        task: TaskSpec,
        workspace_path: Path,
        runner_kind: str,
        adapter_command: str | None = None,
    ) -> RunRequest:
        raise NotImplementedError

    def execute(self, request: RunRequest, observer: RunObserver) -> RunResult:
        return self.executor.execute(request, observer)

