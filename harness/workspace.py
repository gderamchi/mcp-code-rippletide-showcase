from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from difflib import ndiff
from pathlib import Path

from .models import ChangedFile, TaskSpec, WorkspaceContext

COPY_IGNORE = shutil.ignore_patterns(
    '.git',
    '.venv',
    'node_modules',
    'dist',
    'coverage',
    '__pycache__',
    '.pytest_cache',
)


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def snapshot_tree(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root)
        if any(part in {'.git', 'node_modules', '.venv', '__pycache__'} for part in relative_path.parts):
            continue
        try:
            snapshot[str(relative_path)] = path.read_text()
        except UnicodeDecodeError:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            snapshot[str(relative_path)] = f'__binary__:{digest}'
    return snapshot


def build_changed_files(start: dict[str, str], end: dict[str, str]) -> list[ChangedFile]:
    changed: list[ChangedFile] = []
    all_paths = sorted(set(start) | set(end))
    for path in all_paths:
        if start.get(path) == end.get(path):
            continue
        if path not in start:
            added_lines = len(end[path].splitlines())
            changed.append(
                ChangedFile(path=path, status='added', added_lines=added_lines, removed_lines=0)
            )
        elif path not in end:
            removed_lines = len(start[path].splitlines())
            changed.append(
                ChangedFile(path=path, status='deleted', added_lines=0, removed_lines=removed_lines)
            )
        else:
            diff = list(ndiff(start[path].splitlines(), end[path].splitlines()))
            added_lines = sum(1 for line in diff if line.startswith('+ '))
            removed_lines = sum(1 for line in diff if line.startswith('- '))
            changed.append(
                ChangedFile(
                    path=path,
                    status='modified',
                    added_lines=added_lines,
                    removed_lines=removed_lines,
                )
            )
    return changed


def extract_patch_paths(patch_path: Path) -> list[str]:
    paths: list[str] = []
    for line in patch_path.read_text().splitlines():
        if line.startswith('+++ b/'):
            paths.append(line.replace('+++ b/', '', 1))
    return paths


def create_workspace(repo_root: Path, task: TaskSpec) -> WorkspaceContext:
    temp_dir = Path(tempfile.mkdtemp(prefix=f'northstar-{task.task_id}-'))
    workspace_root = temp_dir / repo_root.name
    shutil.copytree(repo_root, workspace_root, ignore=COPY_IGNORE)
    _link_dependency_tree(repo_root / 'node_modules', workspace_root / 'node_modules')
    _link_dependency_tree(repo_root / 'web' / 'node_modules', workspace_root / 'web' / 'node_modules')

    _run(['git', 'init', '-q'], workspace_root)
    _run(['git', 'config', 'user.name', 'Northstar Harness'], workspace_root)
    _run(['git', 'config', 'user.email', 'harness@example.com'], workspace_root)
    _run(['git', 'add', '.'], workspace_root)
    _run(['git', 'commit', '-q', '-m', 'baseline'], workspace_root)

    if task.setup_patch:
        _run(['git', 'apply', task.setup_patch], workspace_root)
        _run(['git', 'add', '.'], workspace_root)
        _run(['git', 'commit', '-q', '-m', f'seed-{task.task_id}'], workspace_root)

    user_change_paths: list[str] = []
    if task.seed_user_changes_patch:
        _run(['git', 'apply', task.seed_user_changes_patch], workspace_root)
        user_change_paths = extract_patch_paths(workspace_root / task.seed_user_changes_patch)

    return WorkspaceContext(
        root=workspace_root,
        task_start_snapshot=snapshot_tree(workspace_root),
        user_change_paths=user_change_paths,
        temp_dir=temp_dir,
    )


def _link_dependency_tree(source: Path, destination: Path) -> None:
    if not source.exists() or destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.symlink_to(source)


def git_status_snapshot(workspace_root: Path) -> list[str]:
    result = _run(['git', 'status', '--short'], workspace_root)
    return [line for line in result.stdout.splitlines() if line]


def diff_snapshot(workspace_root: Path) -> str:
    result = _run(['git', 'diff', '--stat'], workspace_root)
    return result.stdout.strip()
