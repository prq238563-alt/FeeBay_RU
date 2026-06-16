#!/usr/bin/env python3
"""Create GitHub repo and push local main branch. Requires GH_TOKEN with repo scope."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_NAME = ""
DESCRIPTION = "Unofficial Russian localization for FeeBay Simulator (tools + translations)"


def api(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "FeeBay-RU-publisher",
        },
        method=method,
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Set GH_TOKEN or GITHUB_TOKEN", file=sys.stderr)
        return 1

    try:
        user = api("GET", "https://api.github.com/user", token)
    except urllib.error.HTTPError as exc:
        print(exc.read().decode(), file=sys.stderr)
        return 1

    login = user["login"]
    print(f"GitHub user: {login}")

    try:
        repo = api(
            "POST",
            "https://api.github.com/user/repos",
            token,
            {
                "name": REPO_NAME,
                "description": DESCRIPTION,
                "private": False,
                "has_issues": True,
                "auto_init": False,
            },
        )
        print(f"Created: {repo['html_url']}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        if exc.code == 422 and "already exists" in body.lower():
            repo = api("GET", f"https://api.github.com/repos/{login}/{REPO_NAME}", token)
            print(f"Repo exists: {repo['html_url']}")
        else:
            print(body, file=sys.stderr)
            return 1

    remote_https = f"https://github.com/{login}/{REPO_NAME}.git"
    push_url = f"https://x-access-token:{token}@github.com/{login}/{REPO_NAME}.git"

    subprocess.run(["git", "remote", "remove", "origin"], cwd=ROOT, check=False)
    subprocess.run(["git", "remote", "add", "origin", remote_https], cwd=ROOT, check=True)
    push = subprocess.run(
        ["git", "push", "-u", push_url, "main"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if push.returncode != 0:
        print(push.stderr or push.stdout, file=sys.stderr)
        return push.returncode

    subprocess.run(["git", "branch", "--set-upstream-to=origin/main", "main"], cwd=ROOT, check=False)
    print(f"Pushed: {remote_https}")
    print(f"Open: https://github.com/{login}/{REPO_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
