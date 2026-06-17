"""Resolve writable project root for the update toolkit (source tree or portable folder)."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

MARKER = Path("translations") / "strings_ru.json"


def is_repo_root(path: Path) -> bool:
    return (path / MARKER).is_file()


def bundled_data_root() -> Path | None:
    if getattr(sys, "frozen", False):
        root = Path(sys._MEIPASS) / "data"  # type: ignore[attr-defined]
        if root.is_dir():
            return root
    return None


def default_workspace() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "FeeBay_RU_toolkit"
    return Path(__file__).resolve().parent.parent


def discover_repo_root() -> Path | None:
    env = os.environ.get("FEEBAY_RU_ROOT", "").strip()
    if env and is_repo_root(Path(env)):
        return Path(env).resolve()

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        for candidate in (exe_dir, exe_dir.parent, exe_dir.parent.parent):
            if is_repo_root(candidate):
                return candidate
        portable = exe_dir / "FeeBay_RU_toolkit"
        if is_repo_root(portable):
            return portable
        return None

    root = Path(__file__).resolve().parent.parent
    return root if is_repo_root(root) else None


def ensure_workspace(target: Path) -> Path:
    """Create or refresh portable workspace next to the .exe."""
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)

    bundled = bundled_data_root()
    if bundled:
        for name in ("translations", "overrides", "reference"):
            src = bundled / name
            dst = target / name
            if src.is_dir() and not dst.is_dir():
                shutil.copytree(src, dst)

    if not is_repo_root(target):
        raise FileNotFoundError(
            f"Не найден словарь в {target / MARKER}. "
            "Укажите папку клона FeeBay_RU или пересоберите .exe."
        )
    return target
