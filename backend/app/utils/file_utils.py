import os
import shutil
from pathlib import Path
from typing import Optional


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_cleanup_dir(path: Optional[Path]) -> None:
    """Safely remove a temporary directory and all its contents."""
    if path and path.exists() and path.is_dir():
        try:
            shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass


def is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """Ensure target_path does not escape base_dir via directory traversal."""
    try:
        base_dir.resolve()
        target_path.resolve().relative_to(base_dir.resolve())
        return True
    except ValueError:
        return False
