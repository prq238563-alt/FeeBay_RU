"""Headless steps for FeeBay RU maintainer update toolkit."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import contextlib
from collections.abc import Callable
from pathlib import Path

from build_strings_ru import collect_english_strings, should_skip, translate_text
from extract_strings_en import build_payload, read_js_from_asar
from patch_asar import patch_asar
from patch_core import validate_game_dir, _stop_feebay_processes

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

LogFn = Callable[[str], None]


@contextlib.contextmanager
def _capture_stdout(log: LogFn):
    class _Writer:
        def write(self, data: str) -> None:
            for line in data.splitlines():
                line = line.strip()
                if line:
                    log(line)

        def flush(self) -> None:
            pass

    prev = sys.stdout
    sys.stdout = _Writer()  # type: ignore[assignment]
    try:
        yield
    finally:
        sys.stdout = prev


def _resolve_asar(game_dir: Path) -> Path:
    resources = game_dir / "resources"
    original = resources / "app.asar.original"
    current = resources / "app.asar"
    if original.is_file():
        return original
    if current.is_file():
        return current
    raise FileNotFoundError("В папке игры нет app.asar / app.asar.original")


def step_extract(game_dir: Path, repo_root: Path, log: LogFn) -> None:
    asar = _resolve_asar(game_dir)
    log(f"Извлечение строк из {asar.name}…")
    with _capture_stdout(log):
        js, js_rel = read_js_from_asar(asar)
    payload = build_payload(js, source=f"{asar}::{js_rel}")
    out = repo_root / "reference" / "strings_en.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    cards = repo_root / "reference" / "card_names.json"
    cards.write_text(
        json.dumps(sorted(payload.get("card_names", []), key=str.lower), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log(f"Готово: {out.name} ({payload['meta']['unique_count']} строк, бандл {js_rel})")


def step_update_ru(repo_root: Path, game_version: str, log: LogFn) -> None:
    en_path = repo_root / "reference" / "strings_en.json"
    ru_path = repo_root / "translations" / "strings_ru.json"
    cards_path = repo_root / "reference" / "card_names.json"

    if not en_path.is_file():
        raise FileNotFoundError(f"Нет {en_path} — сначала извлеките английские строки.")

    en = json.loads(en_path.read_text(encoding="utf-8"))
    ru = json.loads(ru_path.read_text(encoding="utf-8")) if ru_path.is_file() else {"translations": {}}
    card_names = set(json.loads(cards_path.read_text(encoding="utf-8"))) if cards_path.is_file() else set()

    english = collect_english_strings(en)
    translations: dict[str, str] = dict(ru.get("translations", {}))
    skipped = list(ru.get("skipped", []))
    missing = [s for s in english if s not in translations and not should_skip(s, card_names)]

    log(f"Новых строк для перевода: {len(missing)}")
    if missing:
        if GoogleTranslator is None:
            raise RuntimeError("Нужен deep-translator (pip install deep-translator)")
        translator = GoogleTranslator(source="en", target="ru")
        cache: dict[str, str] = {}
        for i, text in enumerate(missing, 1):
            translations[text] = translate_text(text, cache, translator)
            if i % 10 == 0 or i == len(missing):
                log(f"  переведено {i}/{len(missing)}")

    for text in english:
        if should_skip(text, card_names) and text not in skipped:
            skipped.append(text)

    preserved = {k: ru[k] for k in ("bare_literals", "business_names", "business_taglines") if k in ru}
    out = {
        "meta": {
            "game_version": game_version,
            "total_entries": len(translations),
            "skipped": len(skipped),
            "manual_p0": ru.get("meta", {}).get("manual_p0", 0),
        },
        "skipped": sorted(set(skipped), key=str.lower),
        "translations": dict(sorted(translations.items(), key=lambda x: x[0].lower())),
        **preserved,
    }
    ru_path.parent.mkdir(parents=True, exist_ok=True)
    ru_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Обновлён {ru_path.name} ({len(translations)} записей, версия {game_version})")


def step_merge(repo_root: Path, log: LogFn, lang: str = "ru") -> None:
    import merge_overrides as mo

    mo.REPO_ROOT = repo_root  # type: ignore[misc]
    main_path = repo_root / "translations" / f"strings_{lang}.json"
    override_paths = sorted((repo_root / "overrides").glob(f"*_{lang}.json"))
    if not main_path.is_file():
        raise FileNotFoundError(main_path)
    if not override_paths:
        raise FileNotFoundError(f"Нет overrides/*_{lang}.json")

    main = json.loads(main_path.read_text(encoding="utf-8"))
    merged_count = 0
    for over_path in override_paths:
        over = json.loads(over_path.read_text(encoding="utf-8"))
        main["translations"].update(over.get("translations", {}))
        merged_count += len(over.get("translations", {}))
        for section in ("bare_literals", "business_names", "business_taglines"):
            if section in over:
                main.setdefault(section, {}).update(over[section])
    main.setdefault("meta", {})
    main["meta"]["manual_overrides"] = merged_count
    main["meta"]["total_entries"] = len(main["translations"])
    main_path.write_text(json.dumps(main, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Overrides: {merged_count} из {len(override_paths)} файлов → {main_path.name}")


def step_patch(
    game_dir: Path,
    repo_root: Path,
    log: LogFn,
    *,
    lang: str = "ru",
    install_to_game: bool = True,
    write_release: bool = True,
) -> None:
    check = validate_game_dir(game_dir)
    if not check.ok:
        raise ValueError(check.message)

    dictionary = repo_root / "translations" / f"strings_{lang}.json"
    if not dictionary.is_file():
        raise FileNotFoundError(dictionary)

    resources = game_dir / "resources"
    original = resources / "app.asar.original"
    current = resources / "app.asar"
    if current.is_file():
        try:
            from asar.asar import AsarArchive
            from bundle_paths import find_bundle_js

            with AsarArchive(current, "r") as archive:
                js = archive.read(find_bundle_js(archive.list())).decode("utf-8", errors="replace")
            if "Настройки" not in js and "Settings" in js:
                shutil.copy2(current, original)
                log("Обновлён app.asar.original (чистый английский после Steam).")
        except Exception:
            pass
    if not original.is_file() and current.is_file():
        shutil.copy2(current, original)
        log("Создан app.asar.original")

    release = repo_root / "release"
    release.mkdir(parents=True, exist_ok=True)
    release_asar = release / "app.asar"
    release_unpacked = release / "app.asar.unpacked"
    game_unpacked = resources / "app.asar.unpacked"

    if not release_unpacked.is_dir() and game_unpacked.is_dir():
        shutil.copytree(game_unpacked, release_unpacked)

    log("Сборка патча (нужны Node.js и npx)…")
    _stop_feebay_processes()
    with _capture_stdout(log):
        patch_asar(
            original=original,
            output=release_asar,
            dictionary=dictionary,
            unpacked_dir=release_unpacked,
            lang=lang,
        )
    log(f"release/app.asar: {release_asar.stat().st_size} bytes")

    if install_to_game:
        _stop_feebay_processes()
        shutil.copy2(release_asar, current)
        if release_unpacked.is_dir():
            if game_unpacked.exists():
                shutil.rmtree(game_unpacked)
            shutil.copytree(release_unpacked, game_unpacked)
        log(f"Патч установлен в {current}")

    if write_release and release_unpacked.is_dir() and not install_to_game:
        log(f"Unpacked: {release_unpacked}")


def step_build_player_installer(repo_root: Path, log: LogFn) -> None:
    """Build FeeBay_RU_Installer.exe if PyInstaller is available."""
    if not shutil.which("pyinstaller"):
        raise RuntimeError("PyInstaller не найден в PATH. Установите: pip install pyinstaller")

    release_asar = repo_root / "release" / "app.asar"
    if not release_asar.is_file():
        raise FileNotFoundError("Сначала соберите release/app.asar (шаг «Патч»).")

    spec = repo_root / "tools" / "FeeBay_RU_Installer.spec"
    if not spec.is_file():
        raise FileNotFoundError(spec)

    log("Сборка FeeBay_RU_Installer.exe…")
    subprocess.run(
        ["pyinstaller", "--noconfirm", "--clean", str(spec.name)],
        cwd=repo_root / "tools",
        check=True,
        shell=sys.platform == "win32",
    )
    built = repo_root / "tools" / "dist" / "FeeBay_RU_Installer.exe"
    if not built.is_file():
        raise FileNotFoundError("PyInstaller не создал FeeBay_RU_Installer.exe")

    dest = repo_root / "release" / "FeeBay_RU_Installer.exe"
    shutil.copy2(built, dest)
    log(f"Готово: {dest} ({dest.stat().st_size} bytes)")


def run_full_update(
    game_dir: Path,
    repo_root: Path,
    game_version: str,
    log: LogFn,
    *,
    build_installer: bool = False,
) -> None:
    step_extract(game_dir, repo_root, log)
    step_update_ru(repo_root, game_version, log)
    step_merge(repo_root, log)
    step_patch(game_dir, repo_root, log)
    if build_installer:
        step_build_player_installer(repo_root, log)
    log("Полный цикл обновления завершён.")
