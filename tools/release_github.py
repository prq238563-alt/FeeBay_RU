#!/usr/bin/env python3
"""Create GitHub Release and upload FeeBay_RU_Installer.exe."""
from __future__ import annotations

import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = "prq238563-alt"
REPO = "FeeBay_RU"
INSTALLER = ROOT / "release" / "FeeBay_RU_Installer.exe"


def api(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "FeeBay-RU-release",
        },
        method=method,
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def upload_asset(upload_url: str, token: str, path: Path) -> dict:
    # upload_url ends with {?name,label}
    url = upload_url.split("{")[0] + f"?name={path.name}"
    data = path.read_bytes()
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": ctype,
            "Content-Length": str(len(data)),
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "FeeBay-RU-release",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode())


def game_version() -> str:
    data = json.loads((ROOT / "translations" / "strings_ru.json").read_text(encoding="utf-8"))
    return str(data.get("meta", {}).get("game_version", "0.0.0"))


def main() -> int:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Set GH_TOKEN", file=sys.stderr)
        return 1
    if not INSTALLER.is_file():
        print(f"Missing installer: {INSTALLER}", file=sys.stderr)
        return 1

    ver = game_version()
    tag = f"v{ver}"
    body = (
        f"Русификация FeeBay Simulator (игра v{ver}).\n\n"
        "**Установка:** закройте FeeBay → запустите `FeeBay_RU_Installer.exe` → укажите папку с `FeeBay.exe`.\n\n"
        "Перед обновлением Steam используйте «Восстановить оригинал» в установщике."
    )

    try:
        release = api(
            "POST",
            f"https://api.github.com/repos/{OWNER}/{REPO}/releases",
            token,
            {
                "tag_name": tag,
                "name": f"FeeBay RU {tag}",
                "body": body,
                "draft": False,
                "prerelease": False,
                "make_latest": "true",
            },
        )
    except urllib.error.HTTPError as exc:
        err = exc.read().decode()
        if exc.code == 422 and "already exists" in err.lower():
            releases = api(
                "GET",
                f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{tag}",
                token,
            )
            release = releases
            print(f"Release exists: {release['html_url']}")
        else:
            print(err, file=sys.stderr)
            return 1

    print(f"Release: {release['html_url']}")
    asset = upload_asset(release["upload_url"], token, INSTALLER)
    print(f"Asset: {asset['browser_download_url']}")
    print(f"Size: {INSTALLER.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
