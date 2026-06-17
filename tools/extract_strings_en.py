#!/usr/bin/env python3
"""Extract UI strings from FeeBay JS bundle into reference/strings_en.json format."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from asar.asar import AsarArchive

from apply_patch import SAFE_KEYS
from bundle_paths import find_bundle_js
from patch_asar import STEAM_CANDIDATES, resolve_game_dir

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "reference" / "strings_en.json"
CARD_NAMES_PATH = ROOT / "reference" / "card_names.json"

ARROW_RE = re.compile(r'=>\s*"((?:[^"\\]|\\.)*)"')
DIALOG_RE = re.compile(r'confirm\(\s*"((?:[^"\\]|\\.)*)"')
TEMPLATE_RE = re.compile(
    r'"(arguing with \{name\}[^"]*|chatting with \{name\}[^"]*|'
    r'deep in office gossip with \{name\}[^"]*|'
    r'huddled up with \{name\}[^"]*|'
    r'planning a team lunch with \{name\}[^"]*|'
    r'pulled into \{name\}\'s conversation[^"]*|'
    r'ranking everyone\'s worst flips with \{name\}[^"]*|'
    r'showing \{name\} something on their phone[^"]*|'
    r'stuck hearing \{name\}\'s weekend recap[^"]*|'
    r'trading war stories with \{name\}[^"]*)"'
)


def extract_keyed(js: str, key: str) -> set[str]:
    found: set[str] = set()
    pat = re.compile(rf'{key}:"((?:[^"\\]|\\.)*)"')
    for m in pat.finditer(js):
        s = m.group(1)
        if s and not s.startswith("http"):
            found.add(s)
    pat_s = re.compile(rf"{key}:'((?:[^'\\]|\\.)*)'")
    for m in pat_s.finditer(js):
        s = m.group(1)
        if s and not s.startswith("http"):
            found.add(s)
    return found


def extract_card_names(js: str) -> set[str]:
    names: set[str] = set()
    for m in re.finditer(r'name:"([^"]{2,80})"', js):
        s = m.group(1)
        if re.match(r"^[A-Z]", s) and " " in s:
            names.add(s)
    return names


def read_js_from_asar(asar_path: Path) -> tuple[str, Path]:
    with AsarArchive(asar_path, "r") as archive:
        listing = archive.list()
        js_rel = find_bundle_js(listing)
        return archive.read(js_rel).decode("utf-8"), js_rel


def build_payload(js: str, *, source: str) -> dict:
    by_category: dict[str, list[str]] = {}
    for key in SAFE_KEYS:
        by_category[key] = sorted(extract_keyed(js, key), key=str.lower)

    by_category["text_arrow"] = sorted(
        {m.group(1) for m in ARROW_RE.finditer(js) if "${" in m.group(1)},
        key=str.lower,
    )
    by_category["text_fn"] = sorted(
        {
            m.group(1)
            for m in re.finditer(r'children:"((?:[^"\\]|\\.)*)"', js)
            if len(m.group(1)) > 40 and "search" in m.group(1).lower()
        },
        key=str.lower,
    )
    by_category.setdefault("message", [])

    templates = sorted({m.group(1) for m in TEMPLATE_RE.finditer(js)}, key=str.lower)
    templates.extend(s for s in by_category["text_arrow"] if s not in templates)

    card_names = sorted(extract_card_names(js), key=str.lower)
    all_strings: set[str] = set()
    for vals in by_category.values():
        all_strings.update(vals)
    all_strings.update(templates)

    return {
        "meta": {
            "source": source,
            "unique_count": len(all_strings),
            "card_names_count": len(card_names),
        },
        "by_category": by_category,
        "templates": templates,
        "card_names": card_names,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract English UI strings from FeeBay app.asar")
    parser.add_argument("--game-dir", type=Path, default=None)
    parser.add_argument("--asar", type=Path, default=None, help="Path to app.asar or app.asar.original")
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    parser.add_argument("--js", type=Path, default=None, help="Already-extracted JS bundle")
    args = parser.parse_args()

    if args.js:
        js = args.js.read_text(encoding="utf-8")
        source = str(args.js.resolve())
        js_rel = None
    else:
        if args.asar:
            asar = args.asar.resolve()
        else:
            game_dir = resolve_game_dir(args.game_dir)
            asar = game_dir / "resources" / "app.asar.original"
            if not asar.is_file():
                asar = game_dir / "resources" / "app.asar"
        if not asar.is_file():
            print(f"Missing asar: {asar}", file=sys.stderr)
            return 1
        js, js_rel = read_js_from_asar(asar)
        source = f"{asar}::{js_rel}"

    payload = build_payload(js, source=source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if CARD_NAMES_PATH.parent.exists():
        CARD_NAMES_PATH.write_text(
            json.dumps(sorted(payload.get("card_names", []), key=str.lower), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(f"Wrote {args.out}")
    print(f"  unique strings: {payload['meta']['unique_count']}")
    print(f"  card names: {payload['meta']['card_names_count']}")
    if js_rel:
        print(f"  bundle: {js_rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
