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
CoverageStatus = Literal['covered', 'missing', 'ambiguous', 'not_applicable']
CoverageEvidenceSource = Literal['manifest', 'live_mcp', 'both', 'none']
RuleBenchmarkFamily = Literal[
    'validate_before_conclude',
    'preserve_user_changes',
    'instruction_safety',
    'minimal_change',
    'no_destructive_commands',
    'proper_tool_usage',
    'avoid_unnecessary_questions',
    'branch_sandbox_discipline',
    'no_hallucinated_repo_assumptions',
]


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
class BenchmarkRule:
    id: str
    source_rule_id: str
    category: RuleCategory
    severity: RequirementLevel
    benchmarkable: bool
    normalized_claim: str
    raw_text: str
    source_file: str
    benchmark_family: RuleBenchmarkFamily | None = None
    non_benchmarkable_reason: str = ''


@dataclass(slots=True)
class RuleCoverageResult:
    rule_id: str
    status: CoverageStatus
    evidence_source: CoverageEvidenceSource
    explanation: str


@dataclass(slots=True)
class BenchmarkPrecheck:
    total_rules: int
    benchmarkable_rules: int
    excluded_rules: int
    covered_rules: int
    missing_rules: int
    ambiguous_rules: int
    requires_confirmation: bool
    rules: list[BenchmarkRule]
    coverage_results: list[RuleCoverageResult]


@dataclass(slots=True)
class RuleBenchmarkTask:
    rule_id: str
    condition: str | None
    prompt: str
    detector_rule_id: str
    seed: str
    timeout_seconds: int
    task: TaskSpec


@dataclass(slots=True)
class RuleBenchmarkResult:
    rule_id: str
    condition: str
    verdict: Verdict
    ratio: float
    evidence: list[str]
    duration_ms: int


@dataclass(slots=True)
class RuleComparison:
    rule_id: str
    category: RuleCategory
    md_verdict: Verdict
    mcp_verdict: Verdict
    delta: float
    md_result: RuleBenchmarkResult
    mcp_result: RuleBenchmarkResult


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
    benchmark_rules: list[BenchmarkRule] = field(default_factory=list)
    precheck: BenchmarkPrecheck | None = None
    rule_tasks: list[RuleBenchmarkTask] = field(default_factory=list)
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
