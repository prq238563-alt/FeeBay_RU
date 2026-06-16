# FeeBay RU — русификация FeeBay Simulator

Неофициальная локализация [FeeBay Simulator](https://store.steampowered.com/app/3547880/) (Electron + React).  
В игре нет переключателя языка: весь UI лежит в `resources/app.asar`.

**В репозитории только инструменты и переводы — не файлы игры из Steam.**

[English summary below](#english)

---

## Быстрый старт (игроки)

1. Установите FeeBay через Steam, запустите один раз.
2. Скачайте `FeeBay_RU_Installer.exe` из [Releases](https://github.com/prq238563-alt/FeeBay_RU/releases) *(или соберите сами)*.
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

### Сборка установщика

```powershell
powershell -File tools\build_installer.ps1 -GameDir $game
# → release\FeeBay_RU_Installer.exe
```

Артефакты в `release/` в git не попадают — их прикрепляют к GitHub Release вручную.

---

## Структура проекта

```
FeeBay_RU/
  translations/       # Словари strings_<lang>.json (~780 строк для ru)
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

Релиз: прикрепить `release/FeeBay_RU_Installer.exe` к GitHub Release с номером версии игры из `translations/strings_ru.json` → `meta.game_version`.

---

## Правовая информация

FeeBay Simulator © Lake Country Games. Фан-проект, не связан с разработчиком.  
Не распространяйте файлы игры (`FeeBay.exe`, `app.asar` из Steam) в этом репозитории.

Лицензия инструментов и словарей: [MIT](LICENSE).

---

## English

Community Russian patch for **FeeBay Simulator**. Contains translation JSON, a safe JS patcher (no global replace on game logic ids), PowerShell installer, and PyInstaller GUI.

**Players:** download `FeeBay_RU_Installer.exe` from Releases, point at your Steam install folder.

**Contributors:** edit `overrides/*.json`, run `merge_overrides.py`, then `install_patch.ps1`. See [CONTRIBUTING.md](CONTRIBUTING.md).

Replace `YOUR_USER` in URLs with your GitHub username when forking.
