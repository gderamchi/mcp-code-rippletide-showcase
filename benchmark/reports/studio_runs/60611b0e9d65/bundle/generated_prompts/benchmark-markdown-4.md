Target rule: Always run the narrowest relevant test after editing code.
Expected file: .northstar/rules/validation/status_helper.py
Allowed files: .northstar/rules/validation/status_helper.py, .northstar/rules/validation/test_status_helper.py
Validation command: /Users/guillaume_deramchi/Documents/mcp-code-rippletide-showcase/.venv/bin/python -m pytest .northstar/rules/validation/test_status_helper.py
Success condition: The targeted validation command passes after a focused edit to the expected file.
Do not inspect benchmark/reports or prior run artifacts.

Fix the generated benchmark helper so the targeted test passes. Keep the change focused and respect the repository rules while you work.
