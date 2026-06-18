# FeeBay RU — русификация FeeBay Simulator

Неофициальная локализация [FeeBay Simulator](https://store.steampowered.com/app/3547880/) (Electron + React).  
В игре нет переключателя языка: весь UI лежит в `resources/app.asar`.

**В репозитории только инструменты и переводы — не файлы игры из Steam.**

[English summary below](#english)

---

## Быстрый старт (игроки)

1. Установите FeeBay через Steam, запустите один раз.
2. Скачайте `FeeBay_RU_Installer.exe` из **Releases** этого репозитория *(или соберите сами)*.
3. Закройте игру → запустите установщик → укажите папку с `FeeBay.exe`.
4. Перед обновлением Steam: **«Восстановить оригинал»** → обновление в Steam → снова установить патч.

## Быстрый старт (разработчики)

### Требования

- Windows (установка Steam)
- Python 3.10+
- Node.js (`npx @electron/asar` при сборке asar)
- `pip install -r requirements.txt`

### Установка патча из исходников

```powershell
# Путь к игре (или переменная FEEBAY_GAME_DIR)
$game = "F:\SteamLibrary\steamapps\common\FeeBay"

python tools\merge_overrides.py --lang ru
powershell -File tools\install_patch.ps1 -GameDir $game
```

При первом запуске создаётся резервная копия `resources\app.asar.original`.

### Сборка установщика для игроков

```powershell
powershell -File tools\build_installer.ps1 -GameDir $game
# → release\FeeBay_RU_Installer.exe
```

### Набор обновления (для следующих версий игры)

```powershell
powershell -File tools\build_update_toolkit.ps1
# → release\FeeBay_RU_Update_Toolkit.exe
```

GUI-инструмент: извлечь EN → перевести новое → merge overrides → патч в игру → (опционально) собрать установщик для игроков.  
Рядом с `.exe` можно создать портативную папку `FeeBay_RU_toolkit` или указать клон репозитория.

Артефакты в `release/` в git не попадают — их прикрепляют к GitHub Release вручную.

---

## Структура проекта

```
FeeBay_RU/
  translations/       # Словари strings_<lang>.json (~890 строк для ru)
  overrides/          # Ручные правки (мержатся в словарь)
  reference/          # Английские строки и имена карт (не патчить)
  tools/              # Патчер, установщик, проверки
  release/            # Собранный .exe (локально, не в git)
  .github/workflows/  # CI: JSON + compileall
```

### Файлы перевода

| Файл | Роль |
|------|------|
| `translations/strings_ru.json` | Основной словарь после мержа |
| `overrides/manual_overrides_ru.json` | Туториал, бизнес-лестница |
| `overrides/ui_screens_ru.json` | Инвентарь, улучшения, витрина |
| `overrides/quality_ru.json` | Качество формулировок, справка |
| `overrides/missing_ui_ru.json` | Пустые экраны, блокировки, грейдинг |

Подробнее: [overrides/README.md](overrides/README.md)

### Безопасный патч

`tools/apply_patch.py`:

- заменяет только UI-ключи (`label`, `title`, `body`, `description`, …);
- **не трогает** глобально грейды карт и id фильтров (`PROTECTED_FROM_BARE`);
- точечные вставки для счётчиков, времени суток, настроения рынка (`SPECIAL_REPLACEMENTS`).

**Не переводить:** имена карт, бренды-пародии (ZAG, FeeBay, BidGoblin), внутренние id состояний.

---

## Скрипты

| Скрипт | Описание |
|--------|----------|
| `tools/install_patch.ps1` | Патч установленной игры |
| `tools/patch_asar.py` | Сборка `app.asar` из `.original` |
| `tools/apply_patch.py` | Наложение словаря на JS-бандл |
| `tools/merge_overrides.py` | Мерж `overrides/` → `translations/` |
| `tools/verify_patch.py` | Проверка маркеров и целостности `Of()` |
| `tools/audit_english.py` | Поиск непереведённых строк в оригинальном JS |
| `tools/restore_for_steam.ps1` | Восстановить `app.asar` из бэкапа |
| `tools/fix_steam_stuck_update.ps1` | Застрявшее обновление Steam |
| `tools/build_installer.ps1` | Собрать GUI-установщик |

Переменная `FEEBAY_GAME_DIR` вместо `-GameDir`.

---

## Steam и обновления

Любой патч меняет хеш `app.asar` — Steam будет пытаться вернуть оригинал.

1. `tools/restore_for_steam.ps1`
2. Обновление в Steam
3. Снова `install_patch.ps1`

Ошибка **«Файл с контентом заблокирован»** — см. `fix_steam_stuck_update.ps1`.

---

## Правовая информация

FeeBay Simulator © Lake Country Games. Фан-проект, не связан с разработчиком.  
Не распространяйте файлы игры (`FeeBay.exe`, `app.asar` из Steam) в этом репозитории.

Лицензия инструментов и словарей: [MIT](LICENSE).

---

## English

Community Russian patch for **FeeBay Simulator** — translation JSON, a safe JS patcher (no global replace on game-logic ids), PowerShell installer, and PyInstaller GUI.

**Players:** download `FeeBay_RU_Installer.exe` from [Releases](https://github.com/prq238563-alt/FeeBay_RU/releases), close the game, run the installer, and point it at the folder containing `FeeBay.exe`.

**Forking this repo for another language?** The sections below are a developer manual for building your own locale on top of these tools.

---

### Forking for a new locale

This project is **Russian-first**, but the patch pipeline is designed around a locale code (`--lang`). You can fork it for German, French, Spanish, etc. by adding your own dictionary files and wiring up the few places that are still hard-coded to Russian.

Replace `de` below with your locale code (`fr`, `es`, `pl`, …).

#### What already works out of the box

| Piece | Location / command |
|-------|-------------------|
| Main dictionary | `translations/strings_<lang>.json` (e.g. `strings_de.json`) |
| Hand-tuned fixes | `overrides/*_<lang>.json` (e.g. `manual_overrides_de.json`) |
| English source of truth | `reference/strings_en.json` (shared by all locales) |
| Merge overrides into dictionary | `python tools/merge_overrides.py --lang de` |
| Patch installed game | `python tools/patch_asar.py --lang de` or `powershell -File tools/install_patch.ps1 -Lang de` |

`apply_patch.py` loads `translations/strings_<lang>.json` when you pass `--lang`. Card names and parody brands (ZAG, FeeBay, BidGoblin) stay in English for every locale.

#### Step 1 — Dictionary and overrides (most of the work)

1. Create `translations/strings_de.json` modeled on `strings_ru.json`:
   - `translations` — `"English": "Deutsch"` pairs
   - `skipped` — strings that must stay in English
   - optional sections: `bare_literals`, `business_names`, `business_taglines`
2. Create a set of `overrides/*_de.json` files (mirror the Russian set: `manual_overrides`, `ui_screens`, `quality`, `missing_ui`, …) for phrasing that auto-translation cannot get right.
3. Run:

```powershell
python tools\merge_overrides.py --lang de
powershell -File tools\install_patch.ps1 -GameDir "C:\...\FeeBay" -Lang de
```

This covers the bulk of the UI (~800+ dictionary entries).

See also [translations/README.md](translations/README.md) and [overrides/README.md](overrides/README.md).

#### Step 2 — `apply_patch.py` special replacements (main bottleneck)

`SPECIAL_REPLACEMENTS` and `EXACT_REPLACEMENTS` in `tools/apply_patch.py` contain **Russian strings inlined in Python**. They are *not* read from JSON.

These handle fragments that a simple key→value dictionary cannot patch safely in minified JS:

- pluralization and ternaries (`"1 reward"` / `"2 rewards"`)
- inventory filter tab labels (`all`, `raw`, `grading`, …)
- sort buttons (`recent`, `value`, `profit`, …)
- card condition display (`Near Mint` → localized label) — the `_CONDITION_RU` map
- time-of-day labels, market mood strings, long listing tooltips, etc.

For a new language you must either:

- duplicate those replacement blocks with your target language, or
- refactor them into per-locale config (JSON or a small module) and teach `apply_patch.py` to select by `--lang`.

Without this step, the patch may apply but parts of the UI will stay in English (or Russian if you only change the dictionary).

#### Step 3 — Post-patch verification (`verify_patch.py`)

- `MUST_KEEP` — game-code markers; **language-independent**, update only when the game version changes.
- `LANG_MARKERS` — currently only `"ru"`. Add an entry for your locale with 4–5 strings that prove the patch landed (equivalent of `"Settings"` → your translation).
- `BROKEN_MARKERS` — detects Russian-specific corruption today (translation leaking into code). Add patterns for typical breakage in your language.

Run verification via `patch_asar.py` (it calls `verify_patch.py` automatically) or directly:

```powershell
python tools\verify_patch.py --js path\to\index-*.js --lang de
```

#### Step 4 — Game updates (optional tooling)

These scripts are **Russian-specific** today:

| Script | Role |
|--------|------|
| `build_strings_ru.py` | Auto-translate EN→RU (Google Translate) |
| `update_strings_ru.py` | Merge new English strings into `strings_ru.json` |
| `update_toolkit_core.py` | GUI workflow: extract → translate → merge → patch |

`extract_strings_en.py` is **locale-agnostic** — reuse it as-is after each game update.

For your fork: copy and adapt the Russian scripts, or generalize them to something like `update_strings.py --lang de` with a configurable target language for the translator.

#### Step 5 — Installer and GUI (optional branding)

Still Russian-centric:

- `patch_installer_gui.py` — installer UI strings
- `patch_core.py` — sets `<html lang="ru">` in the patched bundle
- `FeeBay_RU_Update_Toolkit` — locates the repo via `strings_ru.json`, Russian button labels

For a public fork you will likely want your own installer name, icons, and a `-Lang` default matching your locale.

#### What never to translate (any locale)

- Card names (`reference/card_names.json`)
- Parody brands and internal ids: `Damaged`, `Near Mint`, `raw`, `graded`, `unlockReputation`, etc. — listed in `PROTECTED_FROM_BARE` and `MUST_KEEP`
- Condition grades in UI — only via the special replacement maps (like `_CONDITION_RU`), never via blanket dictionary replace

#### Recommended workflow for a new fork

1. Fork the repo; update README title, Releases assets, and any GitHub URLs.
2. Add `strings_<lang>.json` + `overrides/*_<lang>.json`.
3. Port or parameterize `SPECIAL_REPLACEMENTS` for your language.
4. Add `LANG_MARKERS["<lang>"]` (and optional `BROKEN_MARKERS`) in `verify_patch.py`.
5. `merge_overrides.py --lang <lang>` → `install_patch.ps1 -Lang <lang>` → play-test.
6. On each new game version: `extract_strings_en.py` → update dictionary → adjust `MUST_KEEP` if the JS bundle changed → re-patch.

General contribution flow for this Russian repo: [CONTRIBUTING.md](CONTRIBUTING.md).
