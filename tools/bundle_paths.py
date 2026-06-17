"""Resolve Vite bundle paths inside FeeBay app.asar (hash changes each release)."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

ASSETS = Path("dist/assets")
JS_GLOB = re.compile(r"^index-[A-Za-z0-9_-]+\.js$")
CSS_GLOB = re.compile(r"^index-[A-Za-z0-9_-]+\.css$")


def list_asar_paths(asar_list_output: str) -> list[str]:
    paths: list[str] = []
    for line in asar_list_output.splitlines():
        line = line.strip().strip("\\").replace("\\", "/")
        if line:
            paths.append(line)
    return paths


def find_bundle_js(paths: Iterable[str] | None = None, *, assets_dir: Path | None = None) -> Path:
    """Return dist/assets/index-<hash>.js relative to asar root."""
    if assets_dir is not None:
        candidates = [
            p.name for p in assets_dir.iterdir() if p.is_file() and JS_GLOB.match(p.name)
        ]
        if not candidates:
            raise FileNotFoundError(f"No index-*.js in {assets_dir}")
        if len(candidates) > 1:
            candidates.sort(
                key=lambda n: assets_dir.joinpath(n).stat().st_size,
                reverse=True,
            )
        return ASSETS / candidates[0]

    if paths is None:
        raise ValueError("paths or assets_dir required")

    normalized = [str(p).replace("\\", "/").lstrip("/") for p in paths]
    js_files = [
        p for p in normalized if p.startswith("dist/assets/index-") and p.endswith(".js")
    ]
    if not js_files:
        raise FileNotFoundError("No dist/assets/index-*.js in asar listing")
    return Path(sorted(js_files)[-1])


def find_bundle_css(paths: Iterable[str] | None = None, *, assets_dir: Path | None = None) -> Path | None:
    if assets_dir is not None:
        for entry in sorted(assets_dir.iterdir()):
            if entry.is_file() and CSS_GLOB.match(entry.name):
                return ASSETS / entry.name
        return None
    if paths is None:
        return None
    normalized = [str(p).replace("\\", "/").lstrip("/") for p in paths]
    css = [p for p in normalized if p.startswith("dist/assets/index-") and p.endswith(".css")]
    return Path(css[0]) if css else None
