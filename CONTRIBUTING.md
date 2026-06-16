# Contributing

Спасибо за помощь с переводом FeeBay!

## Workflow

1. Fork / branch от `main`.
2. Правки — в `overrides/*_<lang>.json` (не правьте `strings_ru.json` вручную, если можно избежать).
3. `python tools/merge_overrides.py --lang ru`
4. Локально: `powershell -File tools/install_patch.ps1 -GameDir "…\FeeBay"`
5. Проверьте экраны в игре.
6. Pull request с кратким описанием, что переведено.

## Стиль перевода

- Короткие подписи в узких колонках: **Цена**, **Профит**, **Куплено**, **Центр**.
- Сохраняйте пародийные бренды: FeeBay, ZAG, PZA, BidGoblin, Headbook.
- Не переводите имена карт и грейды-состояния как глобальные строки — см. `overrides/README.md`.
- Тон: разговорный, как у игры («флип», «лот», «слаб», «chase» можно оставлять).

## Поиск пропусков

При установленной игре:

```bash
python tools/audit_english.py
# → tools/_audit_en.txt (в git не коммитится)
```

## CI

Push в `main` запускает `.github/workflows/validate.yml` (JSON + compileall).
