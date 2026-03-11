from harness.alignment import McpManifestCompiler, RuleAlignmentEngine
from harness.studio_models import CompiledInstructions, InstructionRule, PromptSource


def test_alignment_engine_matches_mcp_claims() -> None:
    compiled = CompiledInstructions(
        sources=[PromptSource(path='AGENTS.md', content='Use MCP servers.', source_kind='agents')],
        rules=[
            InstructionRule(
                id='agents-1',
                source_kind='agents',
                source_file='AGENTS.md',
                scope_path='/',
                category='mcp',
                requirement_level='hard',
                normalized_claim='use mcp server rippletide',
                raw_text='Use the rippletide MCP server.',
                confidence=0.9,
                enforceability='high',
            )
        ],
    )
    manifest = McpManifestCompiler().compile(
        {
            'mcpServers': {
                'rippletide': {
                    'type': 'http',
                    'url': 'https://mcp.rippletide.com/mcp',
                }
            }
        }
    )

    issues = RuleAlignmentEngine().align(compiled, manifest)

    assert any(issue.status == 'matched' for issue in issues)
    assert any(issue.status == 'extra_in_mcp' for issue in issues)
