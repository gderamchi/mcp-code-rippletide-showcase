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
