# Translation dictionaries

Each locale is a JSON file: `strings_<lang>.json` (e.g. `strings_ru.json`, `strings_de.json`).

## Structure

```json
{
  "meta": { "total_entries": 643 },
  "skipped": ["BidGoblin", "…"],
  "translations": {
    "Settings": "Настройки"
  },
  "bare_literals": {
    "\" Help\"": "\" Справка\""
  },
  "business_names": { "…": "…" },
  "business_taglines": { "…": "…" }
}
```

Hand-tuned entries go in `overrides/*_<lang>.json` (see [overrides/README.md](../overrides/README.md)), then run:

```bash
python tools/merge_overrides.py --lang <lang>
```

## What to skip

See `skipped` in the dictionary and `reference/card_names.json` for card names that must stay in English.
