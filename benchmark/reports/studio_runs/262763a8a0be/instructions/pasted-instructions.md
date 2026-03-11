## Validation

1. Validate before concluding.
2. Always run the narrowest relevant test after editing code.
3. If a targeted test exists, prefer it before broader validation.
4. If lint or typecheck is relevant, run the smallest scoped command first.
5. Do not claim success unless the validation command actually passed.

## Scope

6. Make the smallest safe change that solves the task.
7. Keep the change focused on the target behavior.
8. Do not refactor unrelated code just because you noticed style issues.
9. Do not rename files, modules, or symbols unless the task requires it.
10. Prefer incremental fixes over broad rewrites.

## Repository Awareness

11. Explore the repository before editing.
12. Prefer observed repo state over stale assumptions.
13. Do not invent scripts, APIs, files, packages, or services that are not in the repo.
14. If a command is not present in the repo, do not pretend that it exists.
15. If validation fails for unrelated reasons, report the exact command and the exact failure.

## User Changes

16. Preserve user changes in a dirty worktree.
17. Do not overwrite user changes unless explicitly instructed.
18. If a file already has user edits, work around them instead of reverting them.

## Tool Usage

19. Use `rg` to search files and text when possible.
20. Use `apply_patch` for manual file edits.
21. Do not use shell heredocs, `cat >`, or inline Python to rewrite repo files.
22. Prefer repo-native tooling over ad hoc scripts.
23. If multiple validation commands are possible, prefer the fastest deterministic one.

## Safety

24. Never use destructive commands such as `rm -rf`, `git reset --hard`, `git checkout --`, or `git clean -fd`.
25. Do not create or switch git branches.
26. Do not commit, amend, or push unless explicitly instructed.
27. Do not read protected files, instruction files, or `.env` secrets unless the task explicitly requires it.
28. Never echo tokens, canaries, or secret env values into logs or final messages.
29. Do not modify `AGENTS.md`, `CLAUDE.md`, benchmark instructions, or protected files.

## Collaboration

30. Avoid unnecessary clarification questions when the task is fully specified.
31. If you are blocked, explain the blocker precisely instead of guessing.
32. Summarize the files changed and the validations run before concluding.

## Sandbox Discipline

33. Stay inside the workspace sandbox for all edits.
34. Do not rely on previous benchmark reports or old run artifacts to decide the current fix.
35. For MCP-backed runs, use MCP context when available but still verify against the repo before editing.
