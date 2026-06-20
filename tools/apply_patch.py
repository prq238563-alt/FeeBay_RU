#!/usr/bin/env python3
"""Apply EN->RU UI string replacements to FeeBay minified JS bundle."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DICT = ROOT / "translations" / "strings_ru.json"

def dict_for_lang(lang: str) -> Path:
    return ROOT / "translations" / f"strings_{lang}.json"

SAFE_KEYS = (
    "children",
    "label",
    "desc",
    "description",
    "title",
    "body",
    "cta",
    "ctaLabel",
    "placeholder",
    "text",
    "lock",
    "hint",
    "blurb",
    "confirmLabel",
    "definition",
    "tagline",
)

# Exact quoted fragments in JSX arrays / ternaries (not keyed UI fields).
BARE_LITERALS: dict[str, str] = {}

# Business ladder only — never use global name: replacement (card names use name: too).
BUSINESS_NAMES: dict[str, str] = {}
BUSINESS_TAGLINES: dict[str, str] = {}

# Never bare-replace: used as object keys, filter/sort ids, or condition lookup keys in game logic.
PROTECTED_FROM_BARE = frozenset(
    {
        "Damaged",
        "Heavily Played",
        "Played",
        "Lightly Played",
        "Near Mint",
        "Minty",
        "Gem Candidate",
        "all",
        "raw",
        "grading",
        "graded",
        "showcased",
        "recent",
        "value",
        "profit",
        "rarity",
        "condition",
    }
)

_CONDITION_RU = (
    '{Damaged:"Плохое","Heavily Played":"Сильный износ",Played:"Изношена",'
    '"Lightly Played":"Лёгкий износ","Near Mint":"Почти идеал",Minty:"Как из пака",'
    '"Gem Candidate":"Кандидат в 10"}'
)

SPECIAL_REPLACEMENTS: list[tuple[str, str]] = [
    (
        r'children:\["Claim ",V," reward",V===1\?"":"s"\]',
        'children:["Забрать ",V," ",V===1?"награду":"награды"]',
    ),
    (
        r'," at ",Y\(O\.netWorthRequirement\)," net worth\."\]',
        '," при ",Y(O.netWorthRequirement)," капитала."]',
    ),
    (
        r'," rep"\]',
        '," реп."]',
    ),
    (
        r'children:\[H==="showcased"&&n\.jsx\(S,\{name:"crown",size:11\}\),H,H==="showcased"',
        'children:[H==="showcased"&&n.jsx(S,{name:"crown",size:11}),({all:"Все",raw:"Без грейда",grading:"На грейдинге",graded:"В слабе",showcased:"Витрина"}[H]||H),H==="showcased"',
    ),
    (
        r'\["recent","value","profit","rarity","condition"\]\.map\(H=>n\.jsx\("button",\{onClick:\(\)=>h\(H\),className:`px-3 py-1\.5 rounded-md border \$\{v===H\?"border-feebay-500 bg-feebay-500 text-white font-semibold":"border-line text-ink-700 hover:border-ink-400 bg-card"\}`,children:H\},H\)\)',
        '["recent","value","profit","rarity","condition"].map(H=>n.jsx("button",{onClick:()=>h(H),className:`px-3 py-1.5 rounded-md border ${v===H?"border-feebay-500 bg-feebay-500 text-white font-semibold":"border-line text-ink-700 hover:border-ink-400 bg-card"}`,children:({recent:"Недавние",value:"Цена",profit:"Профит",rarity:"Редкость",condition:"Состояние"}[H]||H)},H))',
    ),
    (
        r"value:B\.status",
        'value:({raw:"Без грейда",graded:"В слабе",grading:"На грейдинге",listed:"В лотах",sold:"Продана"}[B.status]??B.status)',
    ),
    (
        r"value:B\.rawCondition",
        f"value:({_CONDITION_RU}[B.rawCondition]??B.rawCondition)",
    ),
    (
        r"value:e\.rawCondition",
        f"value:({_CONDITION_RU}[e.rawCondition]??e.rawCondition)",
    ),
    (
        r'children:\[e\.rarity," · ",e\.rawCondition\]',
        f'children:[e.rarity," · ",({_CONDITION_RU}[e.rawCondition]??e.rawCondition)]',
    ),
    (
        r'children:\[E\.rarity," · ",E\.rawCondition," · on ",p\.marketplace\]',
        f'children:[E.rarity," · ",({_CONDITION_RU}[E.rawCondition]??E.rawCondition)," · on ",p.marketplace]',
    ),
    (
        r'children:\["Day ",e\.day," wrap-up"\]',
        'children:["Итоги дня ",e.day]',
    ),
    (
        r'children:\["Start day ",e\.day\+1\]',
        'children:["Начать день ",e.day+1]',
    ),
    (
        r'children:\["\+",e\.newCards," new card",e\.newCards===1\?"":"s"," added to your collection today\."\]',
        'children:["+",e.newCards," ",e.newCards===1?"новая карта добавлена":"новых карт добавлено"," в коллекцию сегодня."]',
    ),
    (
        r'children:\["Sell on ",R\]',
        'children:["Продать на ",R]',
    ),
    (
        r'children:\[n\.jsx\(S,\{name:"package",size:12\}\)," Bundle mode"\]',
        'children:[n.jsx(S,{name:"package",size:12})," Режим лота"]',
    ),
    (
        r'children:\["Listing at your ",n\.jsx\("span",\{className:"text-ink-800",children:"reference value"\}\)," gives roughly a 15% sale chance per minute\. List under value for fast flips, over value for jackpot prices but more risk of expiring\. Listings expire after 8 minutes and return to your inventory\. Buyers don\'t always pay instantly - 60% pay on the spot, 30% delay, 10% will cancel and you get your card back \(but lose the time\)\."\]',
        'children:["Выставление по ",n.jsx("span",{className:"text-ink-800",children:"ориентир цены"})," — ~15% шанс продажи в минуту. Ниже рынка — быстрый флип, выше — джекпот, но риск сгорания. Лоты сгорают через 8 минут и возвращаются в инвентарь. Покупатели платят не сразу: 60% сразу, 30% с задержкой, 10% отменят — карта вернётся (но время потеряно)."]',
    ),
    (
        r'children:"reference value"\}\)," gives roughly a 15% sale chance per minute\. List under value for fast flips, over value for jackpot prices but more risk of expiring\. Listings expire after 8 minutes and return to your inventory\. Buyers don\'t always pay instantly - 60% pay on the spot, 30% delay, 10% will cancel and you get your card back \(but lose the time\)\."\]',
        'children:"ориентир цены"})," — ~15% шанс продажи в минуту. Ниже рынка — быстрый флип, выше — джекпот, но риск сгорания. Лоты сгорают через 8 минут и возвращаются в инвентарь. Покупатели платят не сразу: 60% сразу, 30% с задержкой, 10% отменят — карта вернётся (но время потеряно)."]',
    ),
    (
        r'children:y==="all"\?"All listings":y',
        'children:y==="all"?"Все лоты":y',
    ),
    (
        r'children:\[N\.length," active listing",N\.length===1\?"":"s"',
        'children:[N.length," активн",N.length===1?"ый лот":"ых лотов"',
    ),
    (
        r'd\.phase\[0\]\.toUpperCase\(\)\+d\.phase\.slice\(1\)',
        '({morning:"Утро",afternoon:"Полдень",evening:"Вечер",night:"Ночь"}[d.phase]||d.phase)',
    ),
    (
        r'e\.length===0\?\(h="Quiet",p="text-ink-500"\):y>v\?\(h="Bullish",p="text-ebayGreen-700"\):v>y\?\(h="Bearish",p="text-ebayRed-600"\):\(h="Mixed",p="text-ebayYellow-700"\)',
        'e.length===0?(h="Спокойно",p="text-ink-500"):y>v?(h="Рост",p="text-ebayGreen-700"):v>y?(h="Падение",p="text-ebayRed-600"):(h="Смешанно",p="text-ebayYellow-700")',
    ),
    (
        r'children:\["Active trends \(",e\.length,"\)"\]',
        'children:["Активные тренды (",e.length,")"]',
    ),
    (
        r'children:\["Active submissions \(",e\.length,"\)"\]',
        'children:["Активные отправки (",e.length,")"]',
    ),
    (
        r'children:\["Tip: buy the ",',
        'children:["Совет: купи улучшение ",',
    ),
    (
        r'," upgrade to see exact multipliers\."\]',
        '," — увидишь точные множители."]',
    ),
    (
        r'children:\["Chaos: ",\(u\.chaosChance\*100\)\.toFixed\(0\),"% upset"\]',
        'children:["Хаос: ",(u.chaosChance*100).toFixed(0),"% сюрприз"]',
    ),
    (
        r'u==="all"\?"Inventory empty\. Time to go shopping on FeeBay\.":`No \$\{u\} items\.`',
        'u==="all"?"Инвентарь пуст. Пора за покупками на FeeBay.":`Нет карт: ${u}.`',
    ),
    (
        r'`Reach Business Level \$\{i\} to unlock \$\{s\.name\}\.`',
        "`Нужен ур. бизнеса ${i}, чтобы открыть ${s.name}.`",
    ),
    (
        r'pushNotification\("Reach Business Level 2 to hire your first employee\."',
        'pushNotification("Нужен ур. бизнеса 2, чтобы нанять первого сотрудника."',
    ),
    (
        r'children:\["Level ",o\.level," ",n\.jsxs\("span"',
        'children:["Ур. ",o.level," ",n.jsxs("span"',
    ),
    (
        r'children:e\.rawCondition==="Gem Candidate"\?n\.jsx\(Dt,\{term:"gem-candidate",children:e\.rawCondition\}\):e\.rawCondition',
        f'children:e.rawCondition==="Gem Candidate"?n.jsx(Dt,{{term:"gem-candidate",children:"Кандидат в 10"}}):({_CONDITION_RU}[e.rawCondition]??e.rawCondition)',
    ),
    (
        r'sub:`\$\{y\} order\$\{y===1\?"":"s"\} · \$\{e\.length\} active · \$\{r\.length\} pending`',
        "sub:`${y} заказ${y===1?\"\":\"ов\"} · ${e.length} активных · ${r.length} в ожидании`",
    ),
    (
        r'return a<=1&&s<=1\?"Dead-center"',
        'return a<=1&&s<=1?"Идеально по центру"',
    ),
    (
        r':a\+s<=3\?"Slight off-center"',
        ':a+s<=3?"Чуть смещён"',
    ),
    (
        r':a\+s<=6\?"Off-center"',
        ':a+s<=6?"Смещён"',
    ),
    (
        r':a\+s<=10\?"Noticeably off-center"',
        ':a+s<=10?"Заметно смещён"',
    ),
    (
        r':"Heavily off-center"',
        ':"Сильно смещён"',
    ),
    (
        r'children:\[f\.length," card",f\.length===1\?"":"s"," on display"\]',
        'children:[f.length,f.length===1?" карта":" карт"," на витрине"]',
    ),
    (
        r'children:i>0\?`Withdraw \$\{Y\(i\)\}`:"Nothing to withdraw"',
        'children:i>0?`Вывести ${Y(i)}`:"Нечего выводить"',
    ),
]

# Template literals and other fragments where regex is fragile.
EXACT_REPLACEMENTS: list[tuple[str, str]] = [
    (
        '`"Sell on X" instant-sells at ~95% value minus that marketplace\'s fees.`',
        "`«Продать на X» — мгновенная продажа ~за 95% цены минус комиссия площадки.`",
    ),
    (
        '\'"List @ price" posts it to your Online Listings at a price of your choosing.\'',
        "'«Выставить по цене» публикует карту в онлайн-лотах по выбранной цене.'",
    ),
    (
        '\'"Grade @ X" submits to the chosen grading company.\'',
        "'«Grade @ X» отправляет карту в выбранную грейдинговую компанию.'",
    ),
    (
        ':"You don\'t have any raw cards yet - buy or flip one, then come back to redeem."',
        ':"Пока нет сырых карт — купи или перепродай хотя бы одну, потом вернись за купоном."',
    ),
]


def escape_js_string(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def escape_js_template(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )


def sub_count(pattern: str, repl_fn, text: str) -> tuple[str, int]:
    count = 0

    def wrapper(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return repl_fn(match)

    return re.sub(pattern, wrapper, text), count


def escape_js_single_quoted(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def replace_keyed_string(js: str, key: str, en: str, ru: str) -> tuple[str, int]:
    total = 0
    for quote, escaper in (
        ('"', escape_js_string),
        ("`", escape_js_template),
        ("'", escape_js_single_quoted),
    ):
        escaped_en = re.escape(en)
        escaped_ru = escaper(ru)
        pattern = rf"({key}:{quote}){escaped_en}({quote})"
        js, n = sub_count(pattern, lambda m: f"{m.group(1)}{escaped_ru}{m.group(2)}", js)
        total += n
    return js, total


def replace_arrow_string(js: str, en: str, ru: str) -> tuple[str, int]:
    total = 0
    pattern = rf'(text:\(\)=>"){re.escape(en)}(")'
    js, n = sub_count(pattern, lambda m: f'{m.group(1)}{escape_js_string(ru)}{m.group(2)}', js)
    total += n
    pattern = rf"(text:e=>`){re.escape(en)}(`)"
    js, n = sub_count(pattern, lambda m: f"{m.group(1)}{escape_js_template(ru)}{m.group(2)}", js)
    total += n
    return js, total


def replace_bare_quoted(js: str, en: str, ru: str) -> tuple[str, int]:
    total = 0
    pattern = rf'"{re.escape(en)}"'
    js, n = sub_count(pattern, lambda m: f'"{escape_js_string(ru)}"', js)
    total += n
    pattern = rf"'{re.escape(en)}'"
    js, n = sub_count(pattern, lambda m: f"'{escape_js_single_quoted(ru)}'", js)
    total += n
    return js, total


def replace_whitelisted_keyed(js: str, key: str, mapping: dict[str, str]) -> tuple[str, int]:
    total = 0
    for en, ru in sorted(mapping.items(), key=lambda item: -len(item[0])):
        js, n = replace_keyed_string(js, key, en, ru)
        total += n
    return js, total


def apply_special_replacements(js: str) -> tuple[str, int]:
    total = 0
    for old, new in EXACT_REPLACEMENTS:
        count = js.count(old)
        if count:
            js = js.replace(old, new)
            total += count
    for pattern, repl in SPECIAL_REPLACEMENTS:
        js, n = sub_count(pattern, lambda _m: repl, js)
        total += n
    return js, total


def replace_dialog_string(js: str, en: str, ru: str) -> tuple[str, int]:
    total = 0
    escaped = escape_js_string(ru)
    for prefix in ('da("', 'da(`'):
        end = '"' if prefix.endswith('("') else "`"
        esc = escape_js_string(ru) if end == '"' else escape_js_template(ru)
        pattern = rf'({re.escape(prefix)}){re.escape(en)}({re.escape(end)})'
        js, n = sub_count(pattern, lambda m: f"{m.group(1)}{esc}{m.group(2)}", js)
        total += n
    return js, total


def apply_dictionary(
    js: str,
    translations: dict[str, str],
    *,
    bare_literals: dict[str, str] | None = None,
    business_names: dict[str, str] | None = None,
    business_taglines: dict[str, str] | None = None,
    strict: bool,
) -> tuple[str, list[str]]:
    missing: list[str] = []

    bare_literals = bare_literals or {}
    business_names = business_names or {}
    business_taglines = business_taglines or {}
    handled_elsewhere = set(bare_literals) | set(business_names) | set(business_taglines)

    js, _ = apply_special_replacements(js)
    js, _ = replace_whitelisted_keyed(js, "name", business_names)
    js, _ = replace_whitelisted_keyed(js, "tagline", business_taglines)

    for en, ru in sorted(bare_literals.items(), key=lambda item: -len(item[0])):
        if not en or en == ru:
            continue
        js, _ = replace_bare_quoted(js, en, ru)

    for en, ru in sorted(translations.items(), key=lambda item: -len(item[0])):
        if not en or en == ru:
            continue

        replaced = 0
        for key in SAFE_KEYS:
            js, n = replace_keyed_string(js, key, en, ru)
            replaced += n
        js, n = replace_arrow_string(js, en, ru)
        replaced += n
        js, n = replace_dialog_string(js, en, ru)
        replaced += n

        # Dictionary strings may live in JSX fragments as plain quoted literals.
        if replaced == 0 and en not in PROTECTED_FROM_BARE:
            js, n = replace_bare_quoted(js, en, ru)
            replaced += n

        if replaced == 0 and en not in handled_elsewhere:
            missing.append(en)
            if strict:
                raise KeyError(f"String not found in UI contexts: {en!r}")

    return js, missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply translation dictionary to FeeBay JS bundle.")
    parser.add_argument("--js", type=Path, required=True)
    parser.add_argument("--dict", type=Path, default=None)
    parser.add_argument("--lang", default="ru", help="Locale code when --dict is omitted")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--strict", action="store_true", help="Fail if any dictionary key is missing.")
    args = parser.parse_args()

    dict_path = args.dict or dict_for_lang(args.lang)
    if not dict_path.is_file():
        print(f"Dictionary missing: {dict_path}", file=sys.stderr)
        return 1

    payload = json.loads(dict_path.read_text(encoding="utf-8"))
    translations: dict[str, str] = payload.get("translations", payload)
    bare_literals = payload.get("bare_literals", BARE_LITERALS)
    business_names = payload.get("business_names", BUSINESS_NAMES)
    business_taglines = payload.get("business_taglines", BUSINESS_TAGLINES)

    js = args.js.read_text(encoding="utf-8")
    original_len = len(js)

    try:
        patched, missing = apply_dictionary(
            js,
            translations,
            bare_literals=bare_literals,
            business_names=business_names,
            business_taglines=business_taglines,
            strict=args.strict,
        )
    except KeyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_path = args.out or args.js
    out_path.write_text(patched, encoding="utf-8")

    print(f"Patched: {out_path}")
    print(f"Entries: {len(translations)}")
    print(f"Size: {original_len} -> {len(patched)} bytes")
    if missing:
        print(f"Missing ({len(missing)}):")
        for item in missing:
            print(f"  - {item}")
    return 1 if missing and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
