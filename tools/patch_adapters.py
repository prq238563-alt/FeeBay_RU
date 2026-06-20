"""Runtime adapters for FeeBay JS patterns that change between game releases."""

from __future__ import annotations

import re

LISTING_TOOLTIP_START = 'children:["Listing at your ",n.jsx("span",{className:"text-ink-800",children:"reference value"})," gives roughly'
LISTING_TOOLTIP_END = 'but lose the time)."]'
LISTING_TOOLTIP_RU = (
    'children:["Выставление по ",n.jsx("span",{className:"text-ink-800",children:"ориентир цены"}),'
    '" — ~15% шанс продажи в минуту. Ниже рынка — быстрый флип, выше — джекпот, но риск сгорания. '
    "Лоты сгорают через 8 минут и возвращаются в инвентарь. "
    "Покупатели платят не сразу: 60% сразу, 30% с задержкой, 10% отменят — карта вернётся (но время потеряно).\"]"
)

LISTING_TOOLTIP_OLD_START = 'children:"reference value"})," gives roughly'
LISTING_TOOLTIP_OLD_RU = (
    'children:"ориентир цены"})," — ~15% шанс продажи в минуту. Ниже рынка — быстрый флип, выше — джекпот, '
    "но риск сгорания. Лоты сгорают через 8 минут и возвращаются в инвентарь. "
    "Покупатели платят не сразу: 60% сразу, 30% с задержкой, 10% отменят — карта вернётся (но время потеряно).\"]"
)

WITHDRAW_RE = re.compile(
    r'children:i>0\?`Withdraw \$\{(\w+)\(i\)\}`:"Nothing to withdraw"'
)
NET_WORTH_AT_RE = re.compile(
    r'," at ",(\w+)\(([^)]+\.netWorthRequirement)\)," net worth\."\]'
)
FILTER_TABS_RE = re.compile(
    r'children:\[(\w+)==="showcased"&&n\.jsx\(S,\{name:"crown",size:11\}\),\1,\1==="showcased"'
)
SORT_BUTTONS_RE = re.compile(
    r'\["recent","value","profit","rarity","condition"\]\.map\((\w+)=>n\.jsx\("button",\{onClick:\(\)=>h\(\1\),className:`px-3 py-1\.5 rounded-md border \$\{v===\1\?"border-feebay-500 bg-feebay-500 text-white font-semibold":"border-line text-ink-700 hover:border-ink-400 bg-card"\}`,children:\1\},\1\)\)'
)


def _replace_span(js: str, start: str, end: str, repl: str) -> tuple[str, int]:
    i = js.find(start)
    if i < 0:
        return js, 0
    j = js.find(end, i)
    if j < 0:
        return js, 0
    j += len(end)
    return js[:i] + repl + js[j:], 1


def apply_dynamic_patches(js: str) -> tuple[str, list[str]]:
    """Apply special replacements that adapt to renamed minifier symbols."""
    applied: list[str] = []

    js, n = _replace_span(js, LISTING_TOOLTIP_START, LISTING_TOOLTIP_END, LISTING_TOOLTIP_RU)
    if n:
        applied.append("listing-tooltip-jsx")

    js, n = _replace_span(js, LISTING_TOOLTIP_OLD_START, LISTING_TOOLTIP_END, LISTING_TOOLTIP_OLD_RU)
    if n:
        applied.append("listing-tooltip-legacy")

    def withdraw_repl(m: re.Match[str]) -> str:
        sym = m.group(1)
        return f'children:i>0?`Вывести ${{{sym}(i)}}`:"Нечего выводить"'

    js, n = WITHDRAW_RE.subn(withdraw_repl, js)
    if n:
        applied.append("withdraw-button")

    def net_worth_repl(m: re.Match[str]) -> str:
        sym = m.group(1)
        expr = m.group(2)
        return f'," при ",{sym}({expr})," капитала."]'

    js, n = NET_WORTH_AT_RE.subn(net_worth_repl, js)
    if n:
        applied.append("net-worth-at")

    def filter_tabs_repl(m: re.Match[str]) -> str:
        var = m.group(1)
        return (
            f'children:[{var}==="showcased"&&n.jsx(S,{{name:"crown",size:11}}),'
            f'({{all:"Все",raw:"Без грейда",grading:"На грейдинге",graded:"В слабе",showcased:"Витрина"}}[{var}]||{var}),'
            f'{var}==="showcased"'
        )

    js, n = FILTER_TABS_RE.subn(filter_tabs_repl, js)
    if n:
        applied.append("inventory-filter-tabs")

    def sort_buttons_repl(m: re.Match[str]) -> str:
        var = m.group(1)
        return (
            '["recent","value","profit","rarity","condition"].map('
            f'{var}=>n.jsx("button",{{onClick:()=>h({var}),className:`px-3 py-1.5 rounded-md border ${{v==={var}?'
            '"border-feebay-500 bg-feebay-500 text-white font-semibold":"border-line text-ink-700 hover:border-ink-400 bg-card"}}`,'
            f'children:({{recent:"Недавние",value:"Цена",profit:"Профит",rarity:"Редкость",condition:"Состояние"}}[{var}]||{var})}},'
            f'{var}))'
        )

    js, n = SORT_BUTTONS_RE.subn(sort_buttons_repl, js)
    if n:
        applied.append("inventory-sort-buttons")

    return js, applied
