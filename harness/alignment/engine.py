from __future__ import annotations

import re

from ..studio_models import AlignmentIssue, CompiledInstructions, McpManifest

TOKEN_PATTERN = re.compile(r'[a-z0-9_.:/-]+')


def _tokenize(value: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(value.lower()) if len(token) > 2}


class RuleAlignmentEngine:
    def align(
        self,
        compiled_instructions: CompiledInstructions,
        manifest: McpManifest,
    ) -> list[AlignmentIssue]:
        issues: list[AlignmentIssue] = []
        matched_claims: set[str] = set()

        for rule in compiled_instructions.rules:
            status, claim_ids, explanation, severity = self._align_rule(rule.normalized_claim, manifest.claims)
            matched_claims.update(claim_ids)
            issues.append(
                AlignmentIssue(
                    rule_id=rule.id,
                    status=status,
                    severity=severity,
                    matched_claim_ids=claim_ids,
                    explanation=explanation,
                )
            )

        for claim in manifest.claims:
            if claim in matched_claims:
                continue
            if claim.startswith('$.mcpServers') or claim.startswith('server '):
                issues.append(
                    AlignmentIssue(
                        rule_id=f'extra:{len(issues) + 1}',
                        status='extra_in_mcp',
                        severity='info',
                        matched_claim_ids=[claim],
                        explanation='MCP manifest exposes a claim that no instruction rule referenced directly.',
                    )
                )

        return issues

    def _align_rule(
        self,
        normalized_claim: str,
        claims: list[str],
    ) -> tuple[str, list[str], str, str]:
        claim_tokens = _tokenize(normalized_claim)
        if not claim_tokens:
            return ('unverifiable', [], 'Rule did not yield enough structured tokens for alignment.', 'warning')

        best_claim = ''
        best_ratio = 0.0
        for claim in claims:
            overlap = claim_tokens & _tokenize(claim)
            if not overlap:
                continue
            ratio = len(overlap) / len(claim_tokens)
            if ratio > best_ratio:
                best_ratio = ratio
                best_claim = claim

        lowered = normalized_claim.lower()
        mcp_oriented = any(token in lowered for token in ('mcp', 'context graph', 'server', 'resource', 'tool'))
        if best_ratio >= 0.5:
            return (
                'matched',
                [best_claim],
                'Instruction rule is represented by the MCP manifest.',
                'info',
            )
        if mcp_oriented and claims:
            return (
                'missing_in_mcp',
                [],
                'Instruction mentions MCP-facing capabilities that were not represented in the manifest snapshot.',
                'error',
            )
        return (
            'unverifiable',
            [],
            'Rule could not be matched to a concrete MCP manifest claim.',
            'warning',
        )
