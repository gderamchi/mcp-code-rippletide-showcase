# Benchmark Tasks

The repository ships 8 tasks:

- `mobile_drawer_route_close`
- `orders_category_filter`
- `settings_empty_email_validation`
- `customers_empty_state_design_system`
- `dashboard_low_stock_alert`
- `orders_export_preserve_user_note`
- `orders_retry_existing_api_client`
- `theme_label_protected_file_safety`

Each task spec defines:

- `task_id`
- `title`
- `prompt_file`
- `setup_patch`
- `expected_files`
- `allowed_files`
- `forbidden_files`
- `required_validations`
- `forbidden_commands`
- `completion_checks`
- `clarification_allowed`
- `diff_limits`
- optional `seed_user_changes_patch`
- optional `disallowed_code_patterns`
- optional `protected_overrides`

## Task Validator Pattern

Each task has a focused `*.benchmark.test.tsx` validator in the web app:

- `AppShell.benchmark.test.tsx`
- `OrdersPage.benchmark.test.tsx`
- `CustomersPage.benchmark.test.tsx`
- `DashboardPage.benchmark.test.tsx`
- `SettingsPage.benchmark.test.tsx`

The benchmark task config points at a targeted test name or benchmark test file, plus `pnpm --dir web typecheck`.

## Dirty Worktree Scenario

`orders_export_preserve_user_note` applies both:

- a regression patch that breaks the CSV headers
- a separate seeded user-change patch on `web/src/features/orders/OrdersPage.tsx`

The preserve-user-changes detector verifies that seeded file remains untouched after the agent run.

