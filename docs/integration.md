# Integration Guide

## Condition Runners

The repository ships two condition runners:

- `MdConditionRunner`: loads the task prompt plus every markdown file found in `benchmark/instructions/condition_md/`
- `McpConditionRunner`: loads the task prompt plus every JSON file found in `benchmark/instructions/condition_mcp/`

Both produce the same `RunRequest` shape, so the rest of the harness is condition-agnostic.

## Built-In Execution Modes

- `--runner demo`: deterministic mock executor used to validate the benchmark pipeline
- `--runner external`: launches an external adapter command and consumes NDJSON events on stdout

Example:

```bash
.venv/bin/python -m harness.cli run-task \
  --task mobile_drawer_route_close \
  --condition condition_mcp \
  --runner external \
  --adapter-cmd "python3 /abs/path/to/adapter.py {request_file}"
```

If `{request_file}` is omitted, the harness appends the generated `run_request.json` path as the final positional argument.

The repository now ships a Codex CLI adapter:

```bash
codex login
python3 scripts/adapter_codex.py <run_request.json>
```

For the full matrix:

```bash
make benchmark-codex
```

## External Adapter Contract

The harness writes `run_request.json` into the run output directory. That payload includes:

- task metadata
- workspace path
- instruction/context payload
- protected globs
- canary values
- runner metadata

For the current real-integration setup, the payload carries:

- `condition_md`
  - `instruction_bundle`: every markdown instruction file found in `benchmark/instructions/condition_md/`
- `condition_mcp`
  - `mcp_json_bundle`: all MCP-side JSON assets
  - `mcp_server_config`: a merged config built from every JSON asset containing top-level `mcpServers`

The Codex adapter uses `codex exec --json` and config overrides to:

- clear global MCP servers in `condition_md`
- enable only the MCP servers defined by the current `condition_mcp` JSON bundle
- disable Codex multi-agent features for more stable benchmark runs
- add a benchmark wrapper that tells Codex to resolve context/repo conflicts in favor of the actual checked-out repo

The external adapter must stream NDJSON events to stdout. Minimal example:

```json
{"event_type":"agent_message","payload":{"content":"Inspecting the repo first."}}
{"event_type":"tool_call","payload":{"tool":"apply_patch"}}
{"event_type":"run_finished","payload":{"status":"completed","final_message":"task complete"}}
```

The harness normalizes missing envelope fields such as `timestamp`, `run_id`, `task_id`, and `condition`.

## Where To Plug Real Systems

- Real markdown/system-prompt mode: keep `MdConditionRunner`, replace the executor behind `--runner external`
- Real MCP mode: keep `McpConditionRunner`, have the external adapter consume `mcp_server_config` and connect to the configured MCP servers

The task specs, scoring engine, and reporting pipeline do not need to change.
