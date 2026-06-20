"""Discover FeeBay JS integrity markers dynamically (survives minifier renames)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from asar.asar import AsarArchive
from bundle_paths import find_bundle_js

# Stable game-logic identifiers (English, must not be translated away).
STATIC_MUST_KEEP = [
    "unlockReputation",
    "revealGradingSubmission",
    "cancelGradingSubmission",
    "netWorth",
    "shopValue",
    'name:"ZAG Grading"',
    'name:"Bucket Grading"',
    '["all","raw","grading","graded","showcased"]',
    '"Near Mint":[76,90],Minty:[85,95]',
]

GRADE_FN_RE = re.compile(r"function (\w+)\(e\)\{const t=\{Damaged:\[8,24\]")
PAUSE_TOGGLE_RE = re.compile(r"togglePause\(\)\{const (\w+)=t\(\),s=Date\.now\(\);if\(\1\.paused\)")


def read_bundle_js_from_asar(asar_path: Path) -> tuple[str, Path]:
    with AsarArchive(asar_path, "r") as archive:
        listing = archive.list()
        js_rel = find_bundle_js(listing)
        return archive.read(js_rel).decode("utf-8"), js_rel


def read_game_version(asar_path: Path) -> str | None:
    try:
        with AsarArchive(asar_path, "r") as archive:
            for node in archive.list():
                name = str(node).replace("\\", "/")
                if name.endswith("package.json") and "node_modules" not in name:
                    payload = json.loads(archive.read(node))
                    version = payload.get("version")
                    return str(version) if version else None
    except Exception:
        return None
    return None


def discover_dynamic_markers(js: str) -> list[str]:
    """Tokens that move between game releases but stay intact after localization."""
    found: list[str] = []
    grade = GRADE_FN_RE.search(js)
    if grade:
        found.append(grade.group(0))
    pause = PAUSE_TOGGLE_RE.search(js)
    if pause:
        found.append(pause.group(0))
    return found


def discover_must_keep(js: str) -> list[str]:
    markers = [token for token in STATIC_MUST_KEEP if token in js]
    markers.extend(discover_dynamic_markers(js))
    return markers


def discover_missing_markers(js: str) -> list[str]:
    """Markers expected in a vanilla English bundle but absent (needs manual tool update)."""
    missing: list[str] = []
    for token in STATIC_MUST_KEEP:
        if token not in js:
            missing.append(f"static:{token}")
    if not GRADE_FN_RE.search(js):
        missing.append("dynamic:grade-helper Damaged:[8,24]")
    if not PAUSE_TOGGLE_RE.search(js):
        missing.append("dynamic:togglePause paused")
    return missing


def verify_bundle(js: str, *, lang: str, lang_markers: dict[str, list[str]], broken_markers: list[str]) -> list[str]:
    errors: list[str] = []
    for token in discover_must_keep(js):
        if token not in js:
            errors.append(f"missing required token: {token}")
    for token in lang_markers.get(lang, []):
        if token not in js:
            errors.append(f"missing translation marker ({lang}): {token}")
    for token in broken_markers:
        if token in js:
            errors.append(f"found corruption: {token}")
    return errors
