# Northstar Ops Benchmark Repository

Northstar Ops is a local benchmark studio for comparing coding-agent behavior under two context-delivery modes:

- `condition_md`: rules delivered as Markdown / system-prompt context
- `condition_mcp`: rules delivered through MCP context

The benchmark target is rule adherence, not generic model quality. The Studio is built to answer:

- does the agent respect the rules better with `MD` or with `MCP`?
- how many rules from the `.md` are actually represented in the MCP?
- which rules fail only in `MD`, only in `MCP`, or in both?

## What This Repo Contains

- `web/`: the Studio UI and the compact benchmark target app
- `harness/`: Python orchestration, precheck, benchmark execution, scoring, adapters
- `benchmark/`: task fixtures, policies, profiles, prompts, and reports
- `scripts/`: thin wrappers for starting the Studio and external agent adapters
- `protected/`: canary and protected files used by the benchmark
- `docs/`: architecture and integration notes

## Prerequisites

You need these installed locally:

- `python3` with venv support
- `pnpm`
- for real agent runs:
  - `codex` if you want Codex runs
  - `claude` if you want Claude Code runs

## Setup

From the repo root:

```bash
make setup
```

This does all local bootstrap:

- installs frontend dependencies with `pnpm`
- creates `.venv`
- installs the editable Python harness with dev dependencies

## Fastest Way To Try The Project

```bash
make studio
```

Then open:

- `http://localhost:5173/studio`

This starts both:

- the FastAPI backend on `http://127.0.0.1:8008`
- the Vite frontend on `http://localhost:5173`

If you prefer launching them separately:

```bash
make studio-server
pnpm studio:web
```

## How To Use The Studio

The Studio has two flows:

### 1. Quick Start From Profile

Use this for repeatable benchmarks.

Steps:

1. Open `/studio`
2. Pick a saved profile.
   - `Quick demo` is the recommended deterministic local smoke test.
   - `Anthropic demo` is an external-agent run that depends on CLI auth and the shared rippletide MCP.
3. Click `Run precheck`
4. Review the precheck:
   - total rules
   - covered by MCP
   - missing from MCP
   - ambiguous
5. If coverage is acceptable, click `Launch benchmark`
6. If coverage is too low, the Studio warns you before launch
7. Review the final `MD vs MCP` comparison

Profiles live in `benchmark/profiles/`.

### 2. Custom One-Off Config

Use this when you want to test a repo, `.md`, or MCP setup that is not yet saved as a profile.

Steps:

1. Choose the target:
   - `Included benchmark repo`
   - `Another local repo`
2. Choose execution:
   - `demo`
   - `codex`
   - `claude`
   - `custom`
3. Open `Instruction and MCP overrides`
4. Optionally upload instruction files (`.md`, `.txt`)
5. Choose MCP source type:
   - `inline`
   - `file`
   - `command`
6. Run precheck
7. Launch benchmark

## What The Benchmark Actually Does

The benchmark now has two distinct stages.

### Stage 1: Precheck

The precheck is a diagnostic gate, not the benchmark itself.

It does this:

1. parses the `.md` rule set
2. normalizes rules into canonical benchmark rules
3. checks whether those rules are represented in the MCP
4. reports:
   - `covered`
   - `missing`
   - `ambiguous`
   - `not_applicable`

Coverage verification is hybrid:

- manifest / JSON comparison first
- live MCP verification only for unresolved or ambiguous rules

The Studio asks for confirmation before launch if MCP coverage is too low:

- more than `10%` of rules missing, or
- more than `5` missing rules

If you continue anyway, the MCP side is still benchmarked, but missing rules are expected to penalize it.

### Stage 2: Benchmark

This is the real comparison.

The Studio:

1. compiles one executable benchmark task per benchmarkable rule
2. runs every task under `condition_md`
3. runs the same tasks under `condition_mcp`
4. runs the full matrix in parallel
5. compares:
   - `MD adherence`
   - `MCP adherence`
   - rule-by-rule diff
   - category-level diff
   - `md_only`, `mcp_only`, and shared violations

The comparison axis is strictly `MD vs MCP` rule adherence.

## MCP Source Types

The Studio supports three MCP input modes.

### `inline`

Paste MCP JSON directly into the UI.

Use this for:

- quick experiments
- debugging
- temporary configurations

### `file`

Point the Studio at a JSON file.

Use this for:

- versioned benchmark setups
- shared team configs
- reproducible demos

Example profile-backed MCP file:

- `benchmark/profiles/mcp/rippletide.mcp.json`
- `benchmark/profiles/mcp/quick-demo.mcp.json`

### `command`

Provide a local command that prints valid MCP JSON to stdout.

Use this when:

- your MCP comes from another platform
- you can export it via a script or CLI
- you want to avoid copying JSON manually

Example shape:

```bash
python3 scripts/export-mcp.py
```

The Studio consumes this output only. It does not attempt to write back to the external platform.

## Profiles

Profiles are versioned in:

- `benchmark/profiles/`

Current built-in examples:

- `benchmark/profiles/anthropic-demo.json`
- `benchmark/profiles/quick-demo.json`

A profile contains:

- target mode
- execution preset
- instruction sources
- MCP source
- worker count
- tags / demo rank

Profiles are the recommended way to run repeated benchmarks.

For local validation from the repo root, use:

```bash
pnpm web:test -- --run
```

## Built-In Agents

The Studio can currently benchmark:

- `Codex`
- `Claude Code`
- `Custom adapter command`

The backend detects local availability and auth state via:

- `GET /api/agents`

## Running From The CLI

### Start The Studio

```bash
make studio
```

or

```bash
pnpm studio:start
```

### Run The Legacy Demo Matrix

```bash
make benchmark-demo
```

### Run The Legacy External Matrix With Codex

```bash
make benchmark-codex
```

### Run The Legacy External Matrix With Claude Code

```bash
make benchmark-claude
```

### Compare Legacy Benchmark Reports

```bash
make benchmark-compare
```

### Full Repo Validation

```bash
make check
```

## Outputs

### Legacy benchmark outputs

- per-run: `benchmark/reports/runs/<task_id>-<condition>/`
- aggregate: `benchmark/reports/aggregate/<timestamp>/`

### Studio outputs

- run folders: `benchmark/reports/studio_runs/<run_id>/`
- exports: `benchmark/reports/studio_runs/<run_id>-export.zip`

Each Studio run may contain:

- `state.json`
- `summary.json`
- `studio_events.jsonl`
- `bundle/`
- per-task run folders under `runs/`

## How To Read The Result

For a successful benchmark run, focus on:

- `precheck.missing_rules`
- `md_summary.adherence_rate`
- `mcp_summary.adherence_rate`
- `rule_comparisons`
- `category_comparisons`
- `violations`

Interpretation:

- if `MCP` adherence is higher than `MD`, MCP is helping the agent respect the rules better
- if `MD` and `MCP` are close, the delivery method is not materially changing behavior
- if many rules are missing from MCP during precheck, the comparison is weakened and should be treated carefully

## Realistic Limitations

The Studio does not benchmark every possible repo perfectly.

It runs best when the target repo has a detectable test runner:

- `vitest`
- `jest`
- `pytest`

If no supported runner is found, the Studio can still complete precheck and MCP coverage diagnostics, but the execution path becomes limited.

The benchmark is currently strongest on operational and behavioral rules such as:

- validation discipline
- user-change preservation
- protected file safety
- tool usage discipline
- destructive command avoidance

It is less suitable than a hardcoded domain-specific suite for extremely product-specific regressions.

## Troubleshooting

### The backend does not start

Use:

```bash
make setup
make studio-server
```

If that works, prefer `make studio` afterward so backend and frontend start together from the repo-managed environment.

### Codex or Claude Code is not available

Check:

- `GET /api/agents`
- the Studio UI availability badges

You need the relevant CLI installed and authenticated locally.

### The MCP coverage is low

This usually means one of:

- the MCP source is incomplete
- the `.md` has rules not represented in MCP
- the MCP export command returned stale or partial data

In that case:

1. fix the MCP source if possible
2. rerun precheck
3. only continue to benchmark if the warning is acceptable for your use case

## Useful Files

- architecture: `docs/architecture.md`
- integration details: `docs/integration.md`
- scoring: `docs/scoring.md`
- adding tasks: `docs/adding_tasks.md`
- scripts overview: `scripts/README.md`

## Recommended Workflow For Teams

1. put recurring setups into `benchmark/profiles/`
2. prefer MCP `file` or `command` over `inline` for serious runs
3. use the Studio precheck before every benchmark
4. export the run bundle when sharing results
5. compare `MD` vs `MCP` on rule adherence, not only task success
