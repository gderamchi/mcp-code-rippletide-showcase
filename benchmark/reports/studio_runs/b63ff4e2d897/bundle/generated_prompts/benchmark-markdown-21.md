Target rule: Do not invent scripts, APIs, files, packages, or services that are not in the repo.
Expected file: .northstar/rules/validation/status_helper.py
Allowed files: .northstar/rules/validation/status_helper.py, .northstar/rules/validation/test_status_helper.py
Validation command: /Users/guillaume_deramchi/Documents/mcp-code-rippletide-showcase/.venv/bin/python -m pytest .northstar/rules/validation/test_status_helper.py
Success condition: The targeted validation command passes after a focused edit to the expected file.
Do not inspect benchmark/reports or prior run artifacts.

Fix the generated helper using only real repo commands and structures.
