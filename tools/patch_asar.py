#!/usr/bin/env python3
"""Patch FeeBay app.asar with a translation dictionary (Steam-safe repack)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"
APPLY_PATCH = TOOLS / "apply_patch.py"
VERIFY_PATCH = TOOLS / "verify_patch.py"
JS_REL = Path("dist/assets/index-Cv1WB-ch.js")
UNPACK_GLOB = "{**/*.node,**/*.dll,**/*.so,**/*.dylib}"

STEAM_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\FeeBay"),
    Path(r"C:\Program Files\Steam\steamapps\common\FeeBay"),
    Path(r"D:\SteamLibrary\steamapps\common\FeeBay"),
    Path(r"E:\SteamLibrary\steamapps\common\FeeBay"),
    Path(r"F:\SteamLibrary\steamapps\common\FeeBay"),
]


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=check, shell=sys.platform == "win32")


def npx_asar(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return run(["npx", "--yes", "@electron/asar", *args], cwd=cwd, check=check)


def resolve_game_dir(game_dir: Path | None) -> Path:
    if game_dir:
        game_dir = game_dir.resolve()
        if not (game_dir / "FeeBay.exe").is_file():
            raise FileNotFoundError(f"FeeBay.exe not found in {game_dir}")
        return game_dir

    env = os.environ.get("FEEBAY_GAME_DIR", "").strip()
    if env:
        return resolve_game_dir(Path(env))

    for candidate in STEAM_CANDIDATES:
        if (candidate / "FeeBay.exe").is_file():
            return candidate.resolve()

    raise FileNotFoundError(
        "FeeBay not found. Pass --game-dir or set FEEBAY_GAME_DIR to the folder with FeeBay.exe."
    )


def dict_path(lang: str) -> Path:
    return REPO_ROOT / "translations" / f"strings_{lang}.json"


def ensure_original(resources: Path) -> Path:
    original = resources / "app.asar.original"
    current = resources / "app.asar"
    if not original.is_file():
        if current.is_file():
            shutil.copy2(current, original)
            print(f"Backup created: {original}")
        else:
            raise FileNotFoundError(f"Missing {original} and {current}")
    return original


def patch_asar(
    *,
    original: Path,
    output: Path,
    dictionary: Path,
    unpacked_dir: Path,
    lang: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix="feebay-asar-") as tmp:
        work = Path(tmp)
        source_asar = work / "app.asar"
        staging = work / "staging"
        staging.mkdir()
        shutil.copy2(original, source_asar)

        if unpacked_dir.is_dir() and any(unpacked_dir.rglob("*")):
            shutil.copytree(unpacked_dir, work / "app.asar.unpacked")
            print(f"Using existing unpacked files from {unpacked_dir}")

        print("Extracting clean bundle...")
        result = npx_asar("extract", str(source_asar), str(staging), cwd=work, check=False)
        if result.returncode != 0:
            print("Note: extract reported missing unpacked files (steamworks); continuing if JS is present.")

        js_path = staging / JS_REL
        if not js_path.is_file():
            print("Fallback: extract-file for game bundle JS...")
            js_path.parent.mkdir(parents=True, exist_ok=True)
            npx_asar(
                "extract-file",
                str(source_asar),
                str(JS_REL).replace("\\", "/"),
                str(js_path),
                cwd=work,
            )
            if not js_path.is_file():
                raise FileNotFoundError(
                    f"Could not extract {JS_REL}. "
                    "Verify game files in Steam (Integrity check) and retry."
                )

        html_path = staging / "dist" / "index.html"
        print(f"Applying translations ({dictionary.name})...")
        run(
            [
                sys.executable,
                str(APPLY_PATCH),
                "--dict",
                str(dictionary),
                "--js",
                str(js_path),
                "--lang",
                lang,
            ]
        )
        if html_path.is_file():
            html = html_path.read_text(encoding="utf-8")
            html = html.replace('<html lang="en">', f'<html lang="{lang}">')
            html_path.write_text(html, encoding="utf-8")

        run([sys.executable, str(VERIFY_PATCH), "--js", str(js_path), "--lang", lang])

        packed = work / "packed.asar"
        print("Packing app.asar (Steam-compatible size)...")
        npx_asar(
            "pack",
            str(staging),
            str(packed),
            "--unpack",
            UNPACK_GLOB,
            cwd=work,
        )

        orig_size = original.stat().st_size
        new_size = packed.stat().st_size
        ratio = new_size / orig_size if orig_size else 0
        print(f"Size: {orig_size} -> {new_size} bytes (ratio {ratio:.3f})")
        if ratio > 1.15:
            raise RuntimeError(
                "Packed asar is too large — Steam will reject updates. "
                "Aborting to avoid locking game files."
            )

        shutil.copy2(packed, output)
        temp_unpacked = work / "app.asar.unpacked"
        if temp_unpacked.is_dir():
            if unpacked_dir.exists():
                shutil.rmtree(unpacked_dir)
            shutil.copytree(temp_unpacked, unpacked_dir)
            print(f"Updated: {unpacked_dir}")
        print(f"Updated: {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Steam-safe patched app.asar")
    parser.add_argument("--game-dir", type=Path, default=None, help="Folder containing FeeBay.exe")
    parser.add_argument("--lang", default="ru", help="Locale code (loads translations/strings_<lang>.json)")
    parser.add_argument("--dict", type=Path, default=None, help="Override translation dictionary JSON")
    parser.add_argument("--original", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--unpacked", type=Path, default=None)
    args = parser.parse_args()

    dictionary = args.dict or dict_path(args.lang)
    if not dictionary.is_file():
        print(f"Dictionary missing: {dictionary}", file=sys.stderr)
        return 1

    json.loads(dictionary.read_text(encoding="utf-8"))

    game_dir = resolve_game_dir(args.game_dir)
    resources = game_dir / "resources"
    original = args.original or ensure_original(resources)
    output = args.output or (resources / "app.asar")
    unpacked = args.unpacked or (resources / "app.asar.unpacked")

    print(f"Game: {game_dir}")
    print(f"Dictionary: {dictionary}")

    patch_asar(
        original=original,
        output=output,
        dictionary=dictionary,
        unpacked_dir=unpacked,
        lang=args.lang,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
