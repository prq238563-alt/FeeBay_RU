#!/usr/bin/env python3
"""FeeBay localization — GUI installer."""

from __future__ import annotations

import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from patch_core import install_patched_asar, restore_original, validate_game_dir

APP_NAME = "FeeBay — установщик русификации"
SETTINGS_NAME = "feebay_ru_installer.json"

STEAM_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\FeeBay"),
    Path(r"C:\Program Files\Steam\steamapps\common\FeeBay"),
    Path(r"D:\SteamLibrary\steamapps\common\FeeBay"),
    Path(r"E:\SteamLibrary\steamapps\common\FeeBay"),
    Path(r"F:\SteamLibrary\steamapps\common\FeeBay"),
]


def repo_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_path(name: str) -> Path:
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / "data" / name  # type: ignore[attr-defined]
        if bundled.is_file():
            return bundled
    local = repo_root() / "release" / name
    if local.is_file():
        return local
    raise FileNotFoundError(
        f"Bundled patch not found: {name}\n"
        "Build the installer first: tools\\build_installer.ps1"
    )


def settings_path() -> Path:
    return repo_root() / SETTINGS_NAME


def load_last_dir() -> str:
    path = settings_path()
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            saved = data.get("game_dir", "")
            if saved and validate_game_dir(Path(saved)).ok:
                return saved
        except (json.JSONDecodeError, OSError):
            pass

    for candidate in STEAM_CANDIDATES:
        if validate_game_dir(candidate).ok:
            return str(candidate)
    return ""


def save_last_dir(game_dir: str) -> None:
    try:
        settings_path().write_text(
            json.dumps({"game_dir": game_dir}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


class InstallerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.resizable(False, False)
        self.geometry("560x360")
        self._build_ui()
        initial = load_last_dir()
        if initial:
            self.path_var.set(initial)

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 6}
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Укажите папку, где лежит FeeBay.exe (корень игры в Steam):",
            wraplength=520,
        ).pack(anchor=tk.W, **pad)

        row = ttk.Frame(frame)
        row.pack(fill=tk.X, **pad)
        self.path_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.path_var, width=58).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="Обзор…", command=self._browse).pack(side=tk.LEFT, padx=(8, 0))

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, **pad)
        ttk.Button(btns, text="Установить русификацию", command=self._install).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(btns, text="Восстановить оригинал", command=self._restore).pack(side=tk.LEFT)

        ttk.Label(frame, text="Журнал:").pack(anchor=tk.W, padx=12)
        self.log = tk.Text(frame, height=12, wrap=tk.WORD, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        ttk.Label(
            frame,
            text="Перед установкой закройте FeeBay. Перед обновлением в Steam — «Восстановить оригинал».",
            foreground="#555",
            wraplength=520,
        ).pack(anchor=tk.W, padx=12, pady=(0, 4))

    def _log(self, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _browse(self) -> None:
        initial = self.path_var.get().strip() or str(Path.home())
        chosen = filedialog.askdirectory(title="Папка установки FeeBay", initialdir=initial)
        if chosen:
            self.path_var.set(chosen)

    def _game_dir(self) -> Path | None:
        raw = self.path_var.get().strip().strip('"')
        if not raw:
            messagebox.showwarning(APP_NAME, "Сначала выберите папку игры.")
            return None
        return Path(raw)

    def _install(self) -> None:
        game_dir = self._game_dir()
        if not game_dir:
            return

        try:
            patched = resource_path("app.asar")
        except FileNotFoundError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return

        self._log(f"Папка: {game_dir}")
        self._log(f"Патч: {patched}")

        result = install_patched_asar(game_dir, patched)
        self._log(result.message)
        if result.ok:
            save_last_dir(str(game_dir))
            messagebox.showinfo(APP_NAME, result.message)
        else:
            messagebox.showerror(APP_NAME, result.message)

    def _restore(self) -> None:
        game_dir = self._game_dir()
        if not game_dir:
            return
        if not messagebox.askyesno(APP_NAME, "Вернуть оригинальный app.asar из резервной копии?"):
            return
        result = restore_original(game_dir)
        self._log(result.message)
        if result.ok:
            messagebox.showinfo(APP_NAME, result.message)
        else:
            messagebox.showerror(APP_NAME, result.message)


def main() -> None:
    app = InstallerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
