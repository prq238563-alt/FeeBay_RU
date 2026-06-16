#!/usr/bin/env python3
"""Build full Russian translation dictionary from strings_en.json."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except ImportError:  # pragma: no cover
    GoogleTranslator = None

REPO_ROOT = Path(__file__).resolve().parent.parent
EN_PATH = REPO_ROOT / "reference" / "strings_en.json"
P0_PATH = REPO_ROOT / "translations" / "strings_ru_p0.json"
CARD_NAMES_PATH = REPO_ROOT / "reference" / "card_names.json"
OUT_PATH = REPO_ROOT / "translations" / "strings_ru.json"

# Exact English strings to leave untranslated (parody brands / tokens).
SKIP_EXACT = {
    "BidGoblin",
    "ZAG",
    "PZA",
    "Bucket",
    "FeeBay Blue",
    "FB-••••••",
    "FEEBAY GRADED",
    "FeeBay // ADMIN CONSOLE",
    "FeeBay Developer Console",
    "AUTH FAIL",
    "SUSPECT",
    "1st Ed",
    " - ",
    " · ",
    " • ",
    "$100",
    "???",
    "ENTER ›",
    "[ LOG OUT - ESC ]",
    "[ SKIP ]",
    "☠ ROOT ACCESS GRANTED ☠",
    "/cheats",
    "- /admin/secret/do_not_ship_this",
}

# Substrings: if present, skip auto-translation (manual review later).
SKIP_IF_CONTAINS = [
    "FeeBay",
    "BidGoblin",
    "SlabHub",
    "PackTok",
    "Headbook",
    "ZAG",
    "PZA",
    "Golden Goblin",
]

PLACEHOLDER_RE = re.compile(r"(\$\{e\}|\{name\})")


def protect_placeholders(text: str) -> tuple[str, dict[str, str]]:
    tokens: dict[str, str] = {}

    def repl(match: re.Match[str]) -> str:
        key = f"__PH_{len(tokens)}__"
        tokens[key] = match.group(0)
        return key

    return PLACEHOLDER_RE.sub(repl, text), tokens


def restore_placeholders(text: str, tokens: dict[str, str]) -> str:
    for key, value in tokens.items():
        text = text.replace(key, value)
    return text


def should_skip(text: str, card_names: set[str]) -> bool:
    if text in SKIP_EXACT or text in card_names:
        return True
  # pure punctuation / numbers
    if len(text.strip()) <= 1:
        return True
    if re.fullmatch(r"[\W\d_+$]+", text):
        return True
    return any(marker in text for marker in SKIP_IF_CONTAINS)


def collect_english_strings(payload: dict) -> list[str]:
    items: set[str] = set()
    for values in payload.get("by_category", {}).values():
        items.update(values)
    items.update(payload.get("templates", []))
    return sorted(items, key=len, reverse=True)


def translate_text(text: str, cache: dict[str, str], translator: GoogleTranslator) -> str:
    if text in cache:
        return cache[text]

    protected, tokens = protect_placeholders(text)
    try:
        ru = translator.translate(protected)
    except Exception:
        time.sleep(1.5)
        ru = translator.translate(protected)
    ru = restore_placeholders(ru, tokens)
    cache[text] = ru
    time.sleep(0.08)
    return ru


def main() -> None:
    payload = json.loads(EN_PATH.read_text(encoding="utf-8"))
    p0 = json.loads(P0_PATH.read_text(encoding="utf-8")).get("translations", {})

    card_names: set[str] = set()
    if CARD_NAMES_PATH.exists():
        card_names = set(json.loads(CARD_NAMES_PATH.read_text(encoding="utf-8")))

    english = collect_english_strings(payload)
    translations: dict[str, str] = dict(p0)
    skipped: list[str] = []

    translator = None
    if GoogleTranslator is not None:
        translator = GoogleTranslator(source="en", target="ru")

    cache: dict[str, str] = {}

    for text in english:
        if text in translations:
            continue
        if should_skip(text, card_names):
            skipped.append(text)
            continue
        if translator is None:
            raise SystemExit("Install deep-translator: pip install deep-translator")
        translations[text] = translate_text(text, cache, translator)

    preserved: dict = {}
    if OUT_PATH.exists():
        existing = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        for section in ("bare_literals", "business_names", "business_taglines"):
            if section in existing:
                preserved[section] = existing[section]

    out = {
        "meta": {
            "game_version": payload.get("meta", {}).get("source", ""),
            "total_entries": len(translations),
            "skipped": len(skipped),
            "manual_p0": len(p0),
        },
        "skipped": skipped,
        "translations": dict(sorted(translations.items(), key=lambda x: x[0].lower())),
        **preserved,
    }
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(translations)} translations, {len(skipped)} skipped)")


if __name__ == "__main__":
    main()
