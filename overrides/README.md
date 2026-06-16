# Overrides (ручные правки)

Файлы в этой папке **перезаписывают** автоматический словарь при сборке.

```bash
python tools/merge_overrides.py --lang ru
```

Порядок мержа: все `overrides/*_<lang>.json` по алфавиту (поздние ключи побеждают).

| Файл | Назначение |
|------|------------|
| `manual_overrides_ru.json` | Ранние ручные правки, бизнес-лестница, туториал |
| `ui_screens_ru.json` | Экраны: инвентарь, улучшения, витрина |
| `quality_ru.json` | Качество формулировок (Цена/Профит, справка, глоссарий) |
| `missing_ui_ru.json` | Пустые состояния, блокировки меню, грейдинг, тренды |

## Что нельзя переводить глобально

Грейды состояния карт (`Near Mint`, `Minty`, `Damaged`…), id фильтров (`raw`, `graded`) и сортировок — только через `tools/apply_patch.py` (`SPECIAL_REPLACEMENTS` / `PROTECTED_FROM_BARE`). Иначе игра падает при старте.

## Добавить правку

1. Внесите пару `"English": "Русский"` в подходящий `*_ru.json`.
2. `python tools/merge_overrides.py --lang ru`
3. `powershell -File tools/install_patch.ps1 -GameDir "…\FeeBay"`
