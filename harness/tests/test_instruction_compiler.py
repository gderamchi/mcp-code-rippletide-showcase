from pathlib import Path

from harness.compiler.instruction_compiler import InstructionCompiler
from harness.studio_models import PromptSource


def test_instruction_compiler_extracts_actionable_rules() -> None:
    compiler = InstructionCompiler()
    compiled = compiler.compile(
        [
            PromptSource(
                path='AGENTS.md',
                source_kind='agents',
                content=(
                    '## Core rules\n\n'
                    '1. Validate before concluding.\n'
                    '2. Never overwrite user changes in `docs/`.\n'
                    '3. Prefer rg when searching files.\n'
                ),
            )
        ],
        Path.cwd(),
    )

    assert compiled.rules
    assert any(rule.category == 'validation' for rule in compiled.rules)
    assert any(rule.category == 'worktree' for rule in compiled.rules)
    assert any(rule.requirement_level == 'hard' for rule in compiled.rules)


def test_instruction_compiler_extracts_all_studio_default_rules() -> None:
    compiler = InstructionCompiler()
    source = PromptSource(
        path='studio-default.md',
        source_kind='markdown',
        content=(
            'Validate before concluding.\n'
            'Make the smallest safe change.\n'
            'Explore the repository before editing.\n'
            'Do not overwrite user changes.\n'
        ),
    )
    compiled_rules = compiler._extract_deterministically(source)

    assert len(compiled_rules) == 4
    assert any(rule.category == 'scope' and 'smallest safe change' in rule.normalized_claim for rule in compiled_rules)
    assert any(rule.category == 'scope' and 'explore the repository before editing' in rule.normalized_claim for rule in compiled_rules)
