#!/usr/bin/env python3
"""Merge hand-tuned overrides into a locale dictionary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="ru", help="Locale code, e.g. ru, de, fr")
    args = parser.parse_args()

    main_path = REPO_ROOT / "translations" / f"strings_{args.lang}.json"
    override_paths = sorted((REPO_ROOT / "overrides").glob(f"*_{args.lang}.json"))

    if not main_path.is_file():
        raise FileNotFoundError(f"Dictionary not found: {main_path}")
    if not override_paths:
        raise FileNotFoundError(f"No overrides found in overrides/*_{args.lang}.json")

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
    print(f"merged {merged_count} overrides from {len(override_paths)} file(s) into {main_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
