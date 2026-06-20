#!/usr/bin/env python3
"""Sanity checks for patched FeeBay JS bundle."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bundle_markers import verify_bundle as _verify_bundle

LANG_MARKERS: dict[str, list[str]] = {
    "ru": [
        "Настройки",
        "Тёмная тема",
        "Панель",
        "С возвращением, перекуп",
        "Репутация",
    ],
}

# Legacy exports — frozen exe and tests may import these names.
MUST_KEEP = [
    "unlockReputation",
    "revealGradingSubmission",
    "cancelGradingSubmission",
    "netWorth",
    "shopValue",
    'name:"ZAG Grading"',
    'name:"Bucket Grading"',
    'function Pf(e){const t={Damaged:[8,24]',
    'togglePause(){const a=t(),s=Date.now();if(a.paused)',
    '["all","raw","grading","graded","showcased"]',
    '"Near Mint":[76,90],Minty:[85,95]',
]

BROKEN_MARKERS = [
    "unlockРепутация",
    "revealГрейдинг",
    "u.на паузе",
    "a.на паузе",
    "ZAG Грейдинг",
    '"Почти идеал":[76,90]',
    '["Все","Без грейда"',
    'Of("Как из пака")',
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--js", type=Path, required=True)
    parser.add_argument("--lang", default="ru")
    args = parser.parse_args()

    js = args.js.read_text(encoding="utf-8")
    errors = _verify_bundle(
        js,
        lang=args.lang,
        lang_markers=LANG_MARKERS,
        broken_markers=BROKEN_MARKERS,
    )

    if errors:
        print("VERIFY FAILED")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("VERIFY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
