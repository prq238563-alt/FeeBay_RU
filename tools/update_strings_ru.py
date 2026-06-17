#!/usr/bin/env python3
"""Merge new English strings into strings_ru.json for a game update."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

from build_strings_ru import collect_english_strings, should_skip, protect_placeholders, restore_placeholders

ROOT = Path(__file__).resolve().parent.parent
EN_PATH = ROOT / "reference" / "strings_en.json"
RU_PATH = ROOT / "translations" / "strings_ru.json"
CARD_NAMES_PATH = ROOT / "reference" / "card_names.json"


def translate_text(text: str, cache: dict[str, str], translator) -> str:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Add missing EN strings to strings_ru.json")
    parser.add_argument("--game-version", default="0.1.25")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    en = json.loads(EN_PATH.read_text(encoding="utf-8"))
    ru = json.loads(RU_PATH.read_text(encoding="utf-8"))
    card_names = set(json.loads(CARD_NAMES_PATH.read_text(encoding="utf-8"))) if CARD_NAMES_PATH.exists() else set()

    english = collect_english_strings(en)
    translations: dict[str, str] = dict(ru.get("translations", {}))
    skipped = list(ru.get("skipped", []))

    missing = [s for s in english if s not in translations and not should_skip(s, card_names)]
    obsolete = [s for s in translations if s not in english and s not in skipped]

    print(f"English strings: {len(english)}")
    print(f"Existing translations: {len(translations)}")
    print(f"New to translate: {len(missing)}")
    print(f"Obsolete (not in new game): {len(obsolete)}")

    if missing:
        if GoogleTranslator is None:
            raise SystemExit("pip install deep-translator")
        translator = GoogleTranslator(source="en", target="ru")
        cache: dict[str, str] = {}
        for text in missing:
            translations[text] = translate_text(text, cache, translator)
            print(f"  + {text[:70]}{'...' if len(text) > 70 else ''}")

    for text in english:
        if should_skip(text, card_names) and text not in skipped:
            skipped.append(text)

    ru["meta"]["game_version"] = args.game_version
    ru["meta"]["total_entries"] = len(translations)
    ru["meta"]["skipped"] = len(skipped)
    ru["translations"] = dict(sorted(translations.items(), key=lambda x: x[0].lower()))
    ru["skipped"] = sorted(set(skipped), key=str.lower)

    if not args.dry_run:
        RU_PATH.write_text(json.dumps(ru, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {RU_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
