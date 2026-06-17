"""Core install/restore logic for FeeBay Russian patch."""

from __future__ import annotations

import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class InstallResult:
    ok: bool
    message: str


def validate_game_dir(game_dir: Path) -> InstallResult:
    game_dir = game_dir.resolve()
    exe = game_dir / "FeeBay.exe"
    asar = game_dir / "resources" / "app.asar"
    if not game_dir.is_dir():
        return InstallResult(False, "Папка не существует.")
    if not exe.is_file():
        return InstallResult(False, "В папке нет FeeBay.exe — укажите корень установки игры.")
    if not asar.is_file():
        return InstallResult(False, "Не найден resources\\app.asar.")
    return InstallResult(True, "OK")


def backup_original(asar: Path, backup: Path) -> None:
    if not backup.exists():
        shutil.copy2(asar, backup)


def install_patched_asar(game_dir: Path, patched_asar: Path) -> InstallResult:
    check = validate_game_dir(game_dir)
    if not check.ok:
        return check

    asar = game_dir / "resources" / "app.asar"
    backup = game_dir / "resources" / "app.asar.original"
    unpacked = game_dir / "resources" / "app.asar.unpacked"

    if not patched_asar.is_file():
        return InstallResult(False, f"Встроенный патч не найден: {patched_asar}")

    patched_size = patched_asar.stat().st_size
    if backup.is_file():
        orig_size = backup.stat().st_size
        if patched_size > orig_size * 1.15:
            return InstallResult(
                False,
                "Патч повреждён: app.asar слишком большой для Steam.\n"
                "Пересоберите установщик (build_installer.ps1) или запустите install_patch.ps1.",
            )

    try:
        _stop_feebay_processes()
        backup_original(asar, backup)
        shutil.copy2(patched_asar, asar)
        bundled_unpacked = patched_asar.parent / "app.asar.unpacked"
        if not bundled_unpacked.is_dir() and getattr(sys, "frozen", False):
            bundled_unpacked = Path(sys._MEIPASS) / "data" / "app.asar.unpacked"  # type: ignore[attr-defined]
        if bundled_unpacked.is_dir():
            if unpacked.exists():
                shutil.rmtree(unpacked)
            shutil.copytree(bundled_unpacked, unpacked)
    except OSError as exc:
        return InstallResult(False, f"Ошибка записи: {exc}\nЗакройте FeeBay и Steam, затем повторите.")

    return InstallResult(
        True,
        "Русификация установлена.\n"
        f"Резервная копия: {backup}\n"
        "Запустите FeeBay.exe.",
    )


def restore_original(game_dir: Path) -> InstallResult:
    check = validate_game_dir(game_dir)
    if not check.ok:
        return check

    asar = game_dir / "resources" / "app.asar"
    backup = game_dir / "resources" / "app.asar.original"

    if not backup.is_file():
        return InstallResult(False, "Резервная копия app.asar.original не найдена.")

    try:
        _stop_feebay_processes()
        shutil.copy2(backup, asar)
    except OSError as exc:
        return InstallResult(False, f"Ошибка восстановления: {exc}")

    return InstallResult(
        True,
        "Оригинальный app.asar восстановлен.\n"
        "Теперь Steam сможет обновить игру.",
    )


def _stop_feebay_processes() -> None:
    import subprocess

    if sys.platform != "win32":
        return
    subprocess.run(
        ["taskkill", "/IM", "FeeBay.exe", "/F"],
        capture_output=True,
        check=False,
    )


def rebuild_patched_asar_from_bundle(
    game_dir: Path,
    dictionary: Path,
    apply_patch_fn,
) -> Path:
    """Runtime fallback: extract user's asar, patch JS, repack to temp file."""
    import asar  # lazy import for pyinstaller

    from bundle_paths import find_bundle_js

    check = validate_game_dir(game_dir)
    if not check.ok:
        raise ValueError(check.message)

    asar_path = game_dir / "resources" / "app.asar"
    tmp = Path(tempfile.mkdtemp(prefix="feebay-ru-"))
    work = tmp / "work"
    out = tmp / "app.asar"

    try:
        asar.extract_archive(asar_path, work)
        assets = work / "dist" / "assets"
        js_rel = find_bundle_js(assets_dir=assets)
        js = work / js_rel
        html = work / "dist" / "index.html"
        if not js.is_file():
            raise FileNotFoundError("Неожиданная структура app.asar")

        apply_patch_fn(js, dictionary)
        if html.is_file():
            text = html.read_text(encoding="utf-8")
            text = text.replace('<html lang="en">', '<html lang="ru">')
            html.write_text(text, encoding="utf-8")

        asar.create_archive(work, out)
        return out
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
