"""Migrate translation keys when English source strings shift between game versions."""

from __future__ import annotations

import re

# ${Y(500)}, ${V(500)} → ${}
TEMPLATE_RE = re.compile(r"\$\{[^}]+\}")
# Collapse whitespace for fuzzy match
WS_RE = re.compile(r"\s+")


def normalize_key(text: str) -> str:
    t = TEMPLATE_RE.sub("${}", text)
    t = WS_RE.sub(" ", t).strip()
    return t


def migrate_translations(
    translations: dict[str, str],
    english_strings: set[str] | list[str],
) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """
    Copy translations to new English keys when only placeholders/typos changed.
    Returns (updated dict, list of (old_key, new_key) migrations).
    """
    english = set(english_strings)
    out = dict(translations)
    migrations: list[tuple[str, str]] = []

    by_norm: dict[str, list[str]] = {}
    for en in english:
        by_norm.setdefault(normalize_key(en), []).append(en)

    for old_key, ru_value in list(translations.items()):
        if old_key in english:
            continue
        norm = normalize_key(old_key)
        candidates = [c for c in by_norm.get(norm, []) if c not in out or out.get(c) == ru_value]
        if len(candidates) != 1:
            continue
        new_key = candidates[0]
        if new_key == old_key:
            continue
        if new_key not in out:
            out[new_key] = ru_value
            migrations.append((old_key, new_key))
        elif out[new_key] == ru_value and old_key not in english:
            migrations.append((old_key, new_key))

    return out, migrations
