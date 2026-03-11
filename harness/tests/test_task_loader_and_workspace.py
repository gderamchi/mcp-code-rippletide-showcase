from pathlib import Path

from harness.task_loader import load_task
from harness.workspace import create_workspace


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_workspace_applies_setup_and_user_change_patches() -> None:
    task = load_task(REPO_ROOT, 'orders_export_preserve_user_note')
    workspace = create_workspace(REPO_ROOT, task)

    export_file = workspace.root / 'web/src/features/orders/exportOrdersCsv.ts'
    orders_page = workspace.root / 'web/src/features/orders/OrdersPage.tsx'

    assert "Order,Client,Category,State,Owner,Amount" in export_file.read_text()
    assert 'User note: keep the noon carrier handoff note intact.' in orders_page.read_text()
    assert 'web/src/features/orders/OrdersPage.tsx' in workspace.user_change_paths
    assert not (workspace.root / 'benchmark/reports').exists()
