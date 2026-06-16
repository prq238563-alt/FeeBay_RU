#!/usr/bin/env python3
"""Find likely untranslated UI strings in the original FeeBay JS bundle."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from asar.asar import AsarArchive

ROOT = Path(__file__).resolve().parent.parent
JS_REL = Path("dist/assets/index-Cv1WB-ch.js")

STEAM_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\FeeBay"),
    Path(r"C:\Program Files\Steam\steamapps\common\FeeBay"),
    Path(r"D:\SteamLibrary\steamapps\common\FeeBay"),
    Path(r"E:\SteamLibrary\steamapps\common\FeeBay"),
    Path(r"F:\SteamLibrary\steamapps\common\FeeBay"),
]

PATTERNS = [
    r'children:"([A-Z][^"]{4,120})"',
    r'label:"([A-Z][^"]{3,80})"',
    r'title:"([A-Z][^"]{4,120})"',
    r'description:"([A-Z][^"]{10,200})"',
    r'definition:"([A-Z][^"]{20,250})"',
    r"definition:'([A-Z][^']{20,250})'",
    r'body:"([A-Z][^"]{20,250})"',
    r'placeholder:"([A-Z][^"]{4,80})"',
    r'lock:"([A-Z][^"]{4,80})"',
    r'hint:"([A-Z][^"]{4,120})"',
]

SKIP_SUBSTR = (
    "FeeBay", "ZAG", "PZA", "BidGoblin", "Headbook", "JaredsList",
    "http", "svg", "path", "className", "data-", "rgba", "flex",
    "Holo Rare", "Mythic", "Secret", "Emberfang",
)


def resolve_game_dir(path: Path | None) -> Path:
    if path:
        path = path.resolve()
        if not (path / "FeeBay.exe").is_file():
            raise FileNotFoundError(f"FeeBay.exe not found in {path}")
        return path
    env = os.environ.get("FEEBAY_GAME_DIR", "").strip()
    if env:
        return resolve_game_dir(Path(env))
    for candidate in STEAM_CANDIDATES:
        if (candidate / "FeeBay.exe").is_file():
            return candidate.resolve()
    raise FileNotFoundError("FeeBay not found. Pass --game-dir or set FEEBAY_GAME_DIR.")


def resolve_original(game_dir: Path, original: Path | None) -> Path:
    if original:
        return original.resolve()
    backup = game_dir / "resources" / "app.asar.original"
    if backup.is_file():
        return backup
    asar = game_dir / "resources" / "app.asar"
    if asar.is_file():
        return asar
    raise FileNotFoundError("No app.asar.original or app.asar in game resources.")


def audit(js: str) -> list[str]:
    found: set[str] = set()
    for pat in PATTERNS:
        for m in re.finditer(pat, js):
            s = m.group(1).strip()
            if any(x in s for x in SKIP_SUBSTR):
                continue
            if re.match(r"^[A-Z][a-z]+ [A-Z]", s) or " " in s or s.endswith(".") or "(" in s:
                found.add(s)

    for m in re.finditer(r'"([A-Z][a-z]{2,}(?: [a-z][^"]{3,80}){1,8})"', js):
        s = m.group(1)
        if len(s) < 12 or len(s) > 140:
            continue
        if any(x in s for x in SKIP_SUBSTR):
            continue
        if re.search(r"\b(the|and|your|you|for|with|to|on|at|is|are|have|any|buy|see|get)\b", s, re.I):
            found.add(s)

    return sorted(found, key=str.lower)


def main() -> int:
    parser = argparse.ArgumentParser(description="List likely untranslated English UI strings.")
    parser.add_argument("--game-dir", type=Path, default=None)
    parser.add_argument("--original", type=Path, default=None, help="Path to app.asar.original")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "tools" / "_audit_en.txt",
        help="Output report (gitignored)",
    )
    args = parser.parse_args()

    try:
        game_dir = resolve_game_dir(args.game_dir)
        original = resolve_original(game_dir, args.original)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    with AsarArchive(original, "r") as archive:
        js = archive.read(JS_REL).decode("utf-8")

    lines = audit(js)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Game: {game_dir}")
    print(f"Source: {original}")
    print(f"Wrote {len(lines)} candidates to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
