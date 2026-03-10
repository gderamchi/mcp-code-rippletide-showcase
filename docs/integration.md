# Integration Guide

## Condition Runners

The repository ships two condition runners:

- `MdConditionRunner`: loads prompt plus markdown files from `benchmark/instructions/condition_md/`
- `McpConditionRunner`: loads prompt plus structured context fixtures from `benchmark/instructions/condition_mcp/`

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

## External Adapter Contract

The harness writes `run_request.json` into the run output directory. That payload includes:

- task metadata
- workspace path
- instruction/context payload
- protected globs
- canary values
- runner metadata

The external adapter must stream NDJSON events to stdout. Minimal example:

```json
{"event_type":"agent_message","payload":{"content":"Inspecting the repo first."}}
{"event_type":"tool_call","payload":{"tool":"apply_patch"}}
{"event_type":"run_finished","payload":{"status":"completed","final_message":"task complete"}}
```

The harness normalizes missing envelope fields such as `timestamp`, `run_id`, `task_id`, and `condition`.

## Where To Plug Real Systems

- Real markdown/system-prompt mode: keep `MdConditionRunner`, replace the executor behind `--runner external`
- Real MCP mode: keep `McpConditionRunner`, replace the fixture-backed context source with your live MCP provider and use the same external executor contract

The task specs, scoring engine, and reporting pipeline do not need to change.

