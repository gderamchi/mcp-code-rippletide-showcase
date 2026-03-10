# Adding Benchmark Tasks

Each task lives in `benchmark/tasks/<task_id>.json` and references:

- a prompt file under `benchmark/prompts/`,
- a regression setup patch under `benchmark/fixtures/task_setups/`,
- optional seeded user-change patches under `benchmark/fixtures/user_changes/`,
- required validation commands,
- completion checks,
- allowed and forbidden file globs.

Recommended workflow:

1. Start from a green baseline in `web/`.
2. Add or confirm focused tests for the intended behavior.
3. Create a regression patch that breaks only the target behavior.
4. Write the task prompt and config.
5. Add or update harness tests if the scoring surface changes.

