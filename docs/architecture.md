# Architecture

## Product App

Northstar Ops is a Vite React dashboard with a benchmark-friendly structure:

- `web/src/app/`: router and shared settings provider
- `web/src/components/shell/`: route shell and mobile drawer behavior
- `web/src/components/ui/`: reusable primitives such as buttons, cards, empty states, notices, and fields
- `web/src/features/dashboard/`: dashboard page and low-stock alert behavior
- `web/src/features/orders/`: orders page, controller, and CSV export
- `web/src/features/customers/`: customer segmentation and empty-state flow
- `web/src/features/settings/`: invite validation and theme label behavior
- `web/src/lib/api/`: internal mock API layer and seed data
- `web/src/lib/forms/`: shared validation helpers

The base app is green and fully validated. Benchmark tasks do not rely on a broken `main` branch; they seed regressions with task-specific patches in a temp workspace.

## Benchmark Layer

`benchmark/` contains:

- `tasks/`: one JSON task definition per scenario
- `prompts/`: task prompts delivered to the agent
- `instructions/condition_md/`: markdown instruction bundle
- `instructions/condition_mcp/`: structured MCP-style context bundle
- `fixtures/task_setups/`: regression patches applied before each run
- `fixtures/user_changes/`: optional dirty-worktree patches
- `policy.json`: protected paths, command policy, and score weights

## Harness Flow

For each run, the Python harness:

1. Loads the `TaskSpec` and benchmark policy.
2. Copies the repo into a temp workspace.
3. Symlinks installed `node_modules` into the temp workspace for deterministic validation commands.
4. Applies the task regression patch and any seeded user-diff patch.
5. Loads condition-specific instructions.
6. Executes a built-in demo runner or an external adapter.
7. Records normalized JSONL events.
8. Runs required validations.
9. Scores the 10 benchmark rules.
10. Writes per-run and aggregate reports.

## Reporting

Per-run artifacts:

- `events.jsonl`
- `summary.json`
- `changed_files.json`
- `report.md`
- `report.html`

Aggregate artifacts:

- `comparison.json`
- `comparison.csv`
- `comparison.md`

