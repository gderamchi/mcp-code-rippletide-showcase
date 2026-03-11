from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..studio_models import McpManifest, McpServer


def _walk_scalars(value: Any, prefix: str = '$') -> Iterator[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk_scalars(item, f'{prefix}.{key}')
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_scalars(item, f'{prefix}[{index}]')
        return
    yield f'{prefix}={value}'


class McpManifestCompiler:
    def compile(self, raw_config: dict[str, Any]) -> McpManifest:
        servers: list[McpServer] = []
        tools: list[str] = []
        resources: list[str] = []
        prompts: list[str] = []
        claims: list[str] = []

        server_block = raw_config.get('mcpServers') if isinstance(raw_config, dict) else None
        if isinstance(server_block, dict):
            for server_name, payload in server_block.items():
                if not isinstance(payload, dict):
                    continue
                locator = str(payload.get('url') or payload.get('command') or payload.get('transport') or '')
                transport = str(payload.get('type') or ('http' if payload.get('url') else 'command'))
                servers.append(
                    McpServer(
                        id=server_name,
                        transport=transport,
                        locator=locator,
                        enabled=bool(payload.get('enabled', True)),
                    )
                )
                claims.append(f'server {server_name} transport {transport}')
                if locator:
                    claims.append(f'server {server_name} locator {locator}')

                for collection_name, target in (
                    ('tools', tools),
                    ('resources', resources),
                    ('prompts', prompts),
                ):
                    collection = payload.get(collection_name)
                    if isinstance(collection, list):
                        for item in collection:
                            name = self._coerce_name(item)
                            if name:
                                target.append(f'{server_name}:{name}')
                                claims.append(f'{collection_name[:-1]} {server_name}:{name}')

        for item in _walk_scalars(raw_config):
            claims.append(item)

        return McpManifest(
            servers=servers,
            tools=sorted(set(tools)),
            resources=sorted(set(resources)),
            prompts=sorted(set(prompts)),
            claims=sorted(set(claims)),
            provenance={
                'has_servers': bool(servers),
                'claim_count': len(set(claims)),
            },
            raw_config=raw_config,
        )

    def _coerce_name(self, item: Any) -> str | None:
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            for key in ('name', 'id', 'title'):
                value = item.get(key)
                if value:
                    return str(value)
        return None
