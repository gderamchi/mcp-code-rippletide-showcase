PYTHON := python3
VENV := .venv

.PHONY: setup setup-python setup-node web-dev check benchmark-demo benchmark-compare benchmark-codex clean

setup: setup-node setup-python

setup-node:
	pnpm install

setup-python:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[dev]"

web-dev:
	pnpm web:dev

check:
	pnpm web:lint
	pnpm web:typecheck
	pnpm web:test
	$(VENV)/bin/pytest harness/tests

benchmark-demo:
	$(VENV)/bin/python -m harness.cli run-all --runner demo --conditions condition_md condition_mcp

benchmark-compare:
	$(VENV)/bin/python -m harness.cli compare --runs-dir benchmark/reports/runs

benchmark-codex:
	$(VENV)/bin/python -m harness.cli run-all --runner external --conditions condition_md condition_mcp --adapter-cmd "python3 scripts/adapter_codex.py {request_file}"

clean:
	rm -rf $(VENV) web/dist web/coverage
