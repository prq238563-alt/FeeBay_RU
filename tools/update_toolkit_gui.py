#!/usr/bin/env python3
"""FeeBay RU — GUI toolkit for game updates (extract → translate → patch → release)."""

from __future__ import annotations

import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from paths_toolkit import default_workspace, discover_repo_root, ensure_workspace, is_repo_root
from patch_core import validate_game_dir
from update_toolkit_core import (
    run_full_update,
    step_build_player_installer,
    step_extract,
    step_merge,
    step_patch,
    step_update_ru,
)

APP_NAME = "FeeBay RU — набор обновления"
SETTINGS_NAME = "feebay_ru_toolkit.json"

STEAM_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\FeeBay"),
    Path(r"C:\Program Files\Steam\steamapps\common\FeeBay"),
    Path(r"D:\SteamLibrary\steamapps\common\FeeBay"),
    Path(r"E:\SteamLibrary\steamapps\common\FeeBay"),
    Path(r"F:\SteamLibrary\steamapps\common\FeeBay"),
]


def settings_path() -> Path:
    base = discover_repo_root() or default_workspace()
    return base / SETTINGS_NAME


def load_settings() -> dict:
    path = settings_path()
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_settings(game_dir: str, repo_dir: str, version: str) -> None:
    try:
        settings_path().write_text(
            json.dumps(
                {"game_dir": game_dir, "repo_dir": repo_dir, "game_version": version},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError:
        pass


def guess_game_dir() -> str:
    saved = load_settings().get("game_dir", "")
    if saved and validate_game_dir(Path(saved)).ok:
        return saved
    for candidate in STEAM_CANDIDATES:
        if validate_game_dir(candidate).ok:
            return str(candidate)
    return ""


def guess_repo_dir() -> str:
    saved = load_settings().get("repo_dir", "")
    if saved and is_repo_root(Path(saved)):
        return saved
    found = discover_repo_root()
    if found:
        return str(found)
    portable = default_workspace()
    try:
        ensure_workspace(portable)
        return str(portable)
    except FileNotFoundError:
        return str(portable)


def guess_version(repo_dir: str) -> str:
    saved = load_settings().get("game_version", "")
    if saved:
        return saved
    ru = Path(repo_dir) / "translations" / "strings_ru.json"
    if ru.is_file():
        try:
            meta = json.loads(ru.read_text(encoding="utf-8")).get("meta", {})
            return str(meta.get("game_version", "0.1.25"))
        except (json.JSONDecodeError, OSError):
            pass
    return "0.1.25"


class ToolkitApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("640x520")
        self.minsize(560, 480)
        self._busy = False
        self._build_ui()
        self.game_var.set(guess_game_dir())
        self.repo_var.set(guess_repo_dir())
        self.version_var.set(guess_version(self.repo_var.get()))

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 4}
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Папка игры (FeeBay.exe):").pack(anchor=tk.W)
        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, **pad)
        self.game_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.game_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row1, text="…", width=3, command=self._browse_game).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Label(frame, text="Папка проекта FeeBay_RU (словари и overrides):").pack(anchor=tk.W)
        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, **pad)
        self.repo_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.repo_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row2, text="…", width=3, command=self._browse_repo).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(row2, text="Создать рядом", command=self._init_portable).pack(side=tk.LEFT, padx=(6, 0))

        row3 = ttk.Frame(frame)
        row3.pack(fill=tk.X, **pad)
        ttk.Label(row3, text="Версия игры:").pack(side=tk.LEFT)
        self.version_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.version_var, width=12).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Separator(frame).pack(fill=tk.X, pady=8)

        steps = ttk.LabelFrame(frame, text="Шаги", padding=8)
        steps.pack(fill=tk.X, **pad)

        grid = ttk.Frame(steps)
        grid.pack(fill=tk.X)
        buttons = [
            ("1. Извлечь EN", self._run_extract),
            ("2. Перевести новое", self._run_update_ru),
            ("3. Merge overrides", self._run_merge),
            ("4. Патч + в игру", self._run_patch),
            ("5. Установщик игрока", self._run_build_installer),
        ]
        for col, (label, cmd) in enumerate(buttons):
            ttk.Button(grid, text=label, command=cmd).grid(row=0, column=col, padx=3, sticky=tk.EW)
            grid.columnconfigure(col, weight=1)

        ttk.Button(
            frame,
            text="▶ Полный цикл (1→4)",
            command=self._run_full,
        ).pack(fill=tk.X, **pad)

        ttk.Label(frame, text="Журнал:").pack(anchor=tk.W, padx=10)
        self.log = tk.Text(frame, height=14, wrap=tk.WORD, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        ttk.Label(
            frame,
            text="Нужны: Node.js (npx), интернет для автоперевода. Закройте FeeBay перед патчем.",
            foreground="#555",
            wraplength=600,
        ).pack(anchor=tk.W, padx=10)

    def _log(self, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)
        self.update_idletasks()

    def _browse_game(self) -> None:
        path = filedialog.askdirectory(initialdir=self.game_var.get() or str(Path.home()))
        if path:
            self.game_var.set(path)

    def _browse_repo(self) -> None:
        path = filedialog.askdirectory(initialdir=self.repo_var.get() or str(Path.home()))
        if path:
            self.repo_var.set(path)

    def _init_portable(self) -> None:
        target = default_workspace()
        try:
            ensure_workspace(target)
            self.repo_var.set(str(target))
            messagebox.showinfo(APP_NAME, f"Рабочая папка:\n{target}")
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))

    def _paths(self) -> tuple[Path, Path] | None:
        game_raw = self.game_var.get().strip().strip('"')
        repo_raw = self.repo_var.get().strip().strip('"')
        if not game_raw or not repo_raw:
            messagebox.showwarning(APP_NAME, "Укажите папку игры и папку проекта.")
            return None
        game_dir = Path(game_raw)
        repo_dir = Path(repo_raw)
        check = validate_game_dir(game_dir)
        if not check.ok:
            messagebox.showerror(APP_NAME, check.message)
            return None
        try:
            repo_dir = ensure_workspace(repo_dir)
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return None
        save_settings(str(game_dir), str(repo_dir), self.version_var.get().strip())
        return game_dir, repo_dir

    def _run_async(self, title: str, fn) -> None:
        if self._busy:
            messagebox.showwarning(APP_NAME, "Уже выполняется операция.")
            return
        paths = self._paths()
        if not paths:
            return
        game_dir, repo_dir = paths
        version = self.version_var.get().strip() or "0.0.0"

        def worker() -> None:
            self._busy = True
            try:
                self._log(f"—— {title} ——")
                fn(game_dir, repo_dir, version)
                self._log("OK\n")
            except Exception as exc:
                self._log(f"ОШИБКА: {exc}\n")
                self.after(0, lambda: messagebox.showerror(APP_NAME, str(exc)))
            finally:
                self._busy = False

        threading.Thread(target=worker, daemon=True).start()

    def _run_extract(self) -> None:
        self._run_async("Извлечение EN", lambda g, r, v: step_extract(g, r, self._log))

    def _run_update_ru(self) -> None:
        self._run_async(
            "Обновление словаря RU",
            lambda g, r, v: step_update_ru(r, v, self._log),
        )

    def _run_merge(self) -> None:
        self._run_async("Merge overrides", lambda g, r, v: step_merge(r, self._log))

    def _run_patch(self) -> None:
        self._run_async(
            "Патч",
            lambda g, r, v: step_patch(g, r, self._log),
        )

    def _run_build_installer(self) -> None:
        paths = self._paths()
        if not paths:
            return
        _, repo_dir = paths

        def worker() -> None:
            self._busy = True
            try:
                self._log("—— Установщик для игроков ——")
                step_build_player_installer(repo_dir, self._log)
                self._log("OK\n")
            except Exception as exc:
                self._log(f"ОШИБКА: {exc}\n")
                self.after(0, lambda: messagebox.showerror(APP_NAME, str(exc)))
            finally:
                self._busy = False

        threading.Thread(target=worker, daemon=True).start()

    def _run_full(self) -> None:
        self._run_async(
            "Полный цикл",
            lambda g, r, v: run_full_update(g, r, v, self._log, build_installer=False),
        )


def main() -> None:
    ToolkitApp().mainloop()


if __name__ == "__main__":
    main()
