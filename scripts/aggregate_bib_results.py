#!/usr/bin/env python3
"""Aggregate /tmp/bib_results/batch_*.json into docs/bib_verification.md.

Groups problematic entries by status. Cross-references with bib metadata
to give the human reviewer enough context to act on each entry.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = Path("/tmp/bib_results")
BIB_JSONL = Path("/tmp/bib_entries.jsonl")
OUT = ROOT / "docs" / "bib_verification.md"

# Load bib metadata
bib = {}
for line in BIB_JSONL.read_text().splitlines():
    if line.startswith("{"):
        e = json.loads(line)
        bib[e["key"]] = e

# Load all results
results = []
for f in sorted(RESULTS.glob("batch_*.json")):
    data = json.loads(f.read_text())
    for r in data:
        r["_batch"] = f.name
        results.append(r)

# Stats
status_counts = defaultdict(int)
for r in results:
    status_counts[r.get("status", "missing")] += 1

# Orphans / no-URL from bib
orphans = []
no_url = []
verified_keys = {r["key"] for r in results}
for key, e in bib.items():
    if not e["url"]:
        no_url.append(key)
    if not e["citations"] and key not in {"emvco-specs"}:
        orphans.append(key)

# Build report
lines = []
lines.append("# Верификация библиографии")
lines.append("")
lines.append(f"Источник: 568 bib-записей в `assets/bibliography.bib`. Проверено WebFetch: {len(results)} URL.")
lines.append("")
lines.append("## Сводка")
lines.append("")
lines.append("| Статус | Количество |")
lines.append("|---|---|")
for s in ["ok", "dead", "redirect", "mismatch", "paywall", "unclear"]:
    lines.append(f"| {s} | {status_counts.get(s, 0)} |")
lines.append("")
lines.append(f"Всего: {sum(status_counts.values())}")
lines.append("")
lines.append("Дополнительно (не проверялось WebFetch):")
lines.append(f"- bib-записей без URL: {len(no_url)} ({', '.join(no_url) if no_url else '—'})")
lines.append(f"- сиротских записей (не цитируются в .tex): {len(orphans)} ({', '.join(orphans) if orphans else '—'})")
lines.append("")
lines.append("## Легенда статусов")
lines.append("")
lines.append("- **dead** — URL отдаёт 404 или ECONNREFUSED, документ снят/перенесён.")
lines.append("- **redirect** — постоянный редирект на другой контент (URL надо обновить).")
lines.append("- **mismatch** — страница открывается, но содержание не соответствует тому, что заявлено в `title` или контексте цитирования.")
lines.append("- **paywall** — только для подписчиков; верифицировать вручную.")
lines.append("- **unclear** — бот-защита / captcha / таймаут / бинарный PDF; ручная проверка из браузера.")
lines.append("")

# Sections by status (skipping ok)
for status in ["dead", "mismatch", "redirect", "paywall", "unclear"]:
    bucket = [r for r in results if r.get("status") == status]
    if not bucket:
        continue
    lines.append(f"## {status} ({len(bucket)})")
    lines.append("")
    for r in bucket:
        key = r["key"]
        e = bib.get(key, {})
        url = e.get("url", "?")
        title = e.get("title", "?")
        evidence = r.get("evidence", "")
        action = r.get("action", "")
        new_url = r.get("new_url", "")

        # Some agents put the suggested URL into `action` as "replace_url: <url>".
        # Pull it out so it lands in the explicit "предлагаемая замена" line.
        if not new_url and action.startswith("replace_url:"):
            tail = action[len("replace_url:"):].strip()
            # split on first whitespace if there is trailing prose
            m = re.match(r"(https?://\S+)", tail)
            if m:
                new_url = m.group(1)

        # Find first citation location
        cite_loc = ""
        if e.get("citations"):
            c = e["citations"][0]
            cite_loc = f"{c['file']}:{c['line']}"

        lines.append(f"### `{key}`")
        lines.append("")
        lines.append(f"- **title:** {title}")
        lines.append(f"- **url:** <{url}>")
        if cite_loc:
            lines.append(f"- **первое цитирование:** [{cite_loc}]({cite_loc.split(':')[0]}#L{cite_loc.split(':')[1]})")
        lines.append(f"- **evidence:** {evidence}")
        if new_url:
            lines.append(f"- **предлагаемая замена URL:** <{new_url}>")
        else:
            lines.append("- **предлагаемая замена URL:** _нет — агент не нашёл рабочего адреса, действовать по сценарию ниже_")
        if action:
            lines.append(f"- **действие:** {action}")
        # alternatives — зависят и от статуса, и от того, есть ли уже new_url
        if new_url:
            alts = "подставить новый URL из строки **предлагаемая замена URL** выше"
            if status in {"mismatch", "redirect"}:
                alts += "; или переписать прозу так, чтобы она соответствовала старому URL"
        else:
            if status == "dead":
                alts = "найти живой URL вручную (например, через web.archive.org или поиск по точному названию) и подставить; либо снять `\\cite{...}` и переписать утверждение без ссылки"
            elif status == "redirect":
                alts = "пройти по редиректу руками и подставить финальный адрес"
            elif status == "mismatch":
                alts = "найти правильный URL вручную и подставить; либо переписать прозу так, чтобы она соответствовала тому, что реально на странице по текущему URL"
            elif status == "paywall":
                alts = "оставить URL (подписчики прочтут) или найти открытый эквивалент"
            else:  # unclear
                alts = "проверить из браузера: если страница на месте — оставить, если нет — найти замену или переписать"
        lines.append(f"- **варианты:** {alts}")
        lines.append("")
    lines.append("")

# Append no-URL and orphans
lines.append("## Без URL (некликабельные записи)")
lines.append("")
for key in no_url:
    e = bib.get(key, {})
    lines.append(f"- `{key}` — {e.get('title', '?')[:120]}")
lines.append("")

lines.append("## Орфанные записи (не цитируются ни одной .tex)")
lines.append("")
for key in orphans:
    e = bib.get(key, {})
    lines.append(f"- `{key}` — {e.get('title', '?')[:120]}")
lines.append("")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT} ({len(lines)} lines, {OUT.stat().st_size} bytes)")
