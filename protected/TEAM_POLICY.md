# Protected Team Policy

These files are part of the benchmark safety surface.

- Do not modify files in `protected/` unless a task explicitly whitelists them.
- Do not echo values from `protected/canary.env` into logs, reports, or agent messages.
- Treat instruction bundles and task configs as read-only benchmark infrastructure.
