from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any, Literal

from .models import TaskSpec

RuleCategory = Literal[
    'validation',
    'safety',
    'worktree',
    'tooling',
    'scope',
    'quality',
    'mcp',
    'other',
]
RequirementLevel = Literal['hard', 'soft', 'informational']
AlignmentStatus = Literal[
    'matched',
    'missing_in_mcp',
    'extra_in_mcp',
    'conflict',
    'unverifiable',
]
AlignmentSeverity = Literal['info', 'warning', 'error']
TaskOrigin = Literal['template', 'mutation']


@dataclass(slots=True)
class PromptSource:
    path: str
    content: str
    source_kind: str


@dataclass(slots=True)
class InstructionRule:
    id: str
    source_kind: str
    source_file: str
    scope_path: str
    category: RuleCategory
    requirement_level: RequirementLevel
    normalized_claim: str
    raw_text: str
    confidence: float
    enforceability: str


@dataclass(slots=True)
class InstructionConflict:
    rule_ids: list[str]
    reason: str


@dataclass(slots=True)
class CompiledInstructions:
    sources: list[PromptSource]
    rules: list[InstructionRule]
    conflicts: list[InstructionConflict] = field(default_factory=list)
    shadowed_rules: list[str] = field(default_factory=list)
    low_confidence_rules: list[str] = field(default_factory=list)
    extraction_mode: str = 'deterministic'


@dataclass(slots=True)
class McpServer:
    id: str
    transport: str
    locator: str
    enabled: bool


@dataclass(slots=True)
class McpManifest:
    servers: list[McpServer]
    tools: list[str]
    resources: list[str]
    prompts: list[str]
    claims: list[str]
    provenance: dict[str, Any]
    raw_config: dict[str, Any]


@dataclass(slots=True)
class AlignmentIssue:
    rule_id: str
    status: AlignmentStatus
    severity: AlignmentSeverity
    matched_claim_ids: list[str]
    explanation: str


@dataclass(slots=True)
class RepoCapabilities:
    root: Path
    package_manager: str | None
    language: str | None
    test_runner: str | None
    validation_command_template: str | None
    available_scripts: list[str] = field(default_factory=list)
    supported: bool = False
    support_reason: str = ''


@dataclass(slots=True)
class GeneratedTask:
    task_id: str
    origin: TaskOrigin
    prompt: str
    required_validations: list[str]
    seed_patch: str | None
    expected_outcome: str
    diff_budget: dict[str, int]
    supported: bool = True
    support_reason: str = ''
    task: TaskSpec | None = None


@dataclass(slots=True)
class DynamicRunBundle:
    bundle_root: Path
    source_root: Path
    inputs: dict[str, Any]
    compiled_instructions: CompiledInstructions
    mcp_manifest: McpManifest
    alignment_issues: list[AlignmentIssue]
    capabilities: RepoCapabilities
    generated_tasks: list[GeneratedTask]
    run_summaries: list[dict[str, Any]] = field(default_factory=list)
    aggregate: dict[str, Any] = field(default_factory=dict)


def studio_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: studio_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: studio_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [studio_jsonable(item) for item in value]
    return value
