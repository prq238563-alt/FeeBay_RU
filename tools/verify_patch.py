#!/usr/bin/env python3
"""Sanity checks for patched FeeBay JS bundle."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LANG_MARKERS: dict[str, list[str]] = {
    "ru": [
        "Настройки",
        "Тёмная тема",
        "Панель",
        "С возвращением, перекуп",
        "Репутация",
    ],
}

MUST_KEEP = [
    "unlockReputation",
    "revealGradingSubmission",
    "cancelGradingSubmission",
    "netWorth",
    "shopValue",
    "togglePause(){const a=t(),s=Date.now();if(a.paused)",
    'name:"ZAG Grading"',
    'name:"Bucket Grading"',
    'function Pf(e){const t={Damaged:[8,24]',
    '["all","raw","grading","graded","showcased"]',
    '"Near Mint":[76,90],Minty:[85,95]',
]

BROKEN_MARKERS = [
    "unlockРепутация",
    "revealГрейдинг",
    "u.на паузе",
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
    errors: list[str] = []

    for token in MUST_KEEP:
        if token not in js:
            errors.append(f"missing required token: {token}")

    for token in LANG_MARKERS.get(args.lang, []):
        if token not in js:
            errors.append(f"missing translation marker ({args.lang}): {token}")

    for token in BROKEN_MARKERS:
        if token in js:
            errors.append(f"found corruption: {token}")

    if errors:
        print("VERIFY FAILED")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("VERIFY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
