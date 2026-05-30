#!/usr/bin/env python3
"""Из свода аудита делает: (1) round-1 план правок по файлам (с дорезолвом путей,
фолдингом consistency, маршрутом generated→генератор), (2) round-2 отложенные
координатные правки, (3) свежие docs/reflow/*.md."""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
res = json.loads((ROOT / "build" / "reflow-audit-result.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "build" / "reflow-manifest.json").read_text(encoding="utf-8"))

gen_for_svg = {}
pat = re.compile(r'figures_dir\(\)\s*/\s*"([^"]+)"\s*/\s*"([^"]+\.svg)"')
for g in (ROOT / "scripts" / "figures").glob("gen_*.py"):
    for m in pat.finditer(g.read_text(encoding="utf-8", errors="ignore")):
        gen_for_svg[f"{m.group(1)}/{m.group(2)}"] = f"scripts/figures/{g.name}"
tex_for_figdir = {u["fig_dir"]: u["tex"] for u in manifest if u["fig_dir"]}

# индекс basename->полный путь svg
svg_by_name = {}
for p in (ROOT / "assets" / "figures").rglob("*.svg"):
    svg_by_name.setdefault(p.name, str(p.relative_to(ROOT)))


def resolve(p):
    if not p:
        return ""
    p = p.strip().strip("`")
    for pre in ("assets/", "src/", "scripts/", "samples/"):
        i = p.find(pre)
        if i >= 0:
            return p[i:]
    if p.endswith(".svg") and p in svg_by_name:  # bare basename
        return svg_by_name[p]
    return p


def is_round2(cat, fix):
    return ("looseness" in (fix or "").lower()) or cat == "widow-orphan"


records = []
for c in res.get("review", []):
    for f in c.get("findings", []):
        tgt = resolve(f.get("target", ""))
        rel = "/".join(Path(tgt).parts[-2:]) if tgt.endswith(".svg") else ""
        if rel in gen_for_svg:
            tgt = gen_for_svg[rel]
        kind = ("generator" if tgt.startswith("scripts/figures/") else "svg" if tgt.endswith(".svg")
                else "tex" if tgt.endswith(".tex") else "py" if tgt.endswith(".py")
                else "bib" if tgt.endswith(".bib") else "?")
        records.append({"src": "review", "unit": c["unit"], "file": tgt, "kind": kind,
                        "page": f.get("page"), "severity": f["severity"], "category": f["category"],
                        "problem": f["problem"], "fix": f["fix"],
                        "round": 2 if is_round2(f["category"], f["fix"]) else 1})

for d in res.get("figures", []):
    for fig in d.get("figures", []):
        svg = resolve(fig.get("svg", ""))
        rel = "/".join(Path(svg).parts[-2:]) if svg else ""
        for it in fig.get("issues", []):
            ft = it.get("fixTarget", "svg")
            if ft == "generator" or rel in gen_for_svg:
                tgt, kind = gen_for_svg.get(rel, svg), "generator"
            elif ft == "tex":
                tgt, kind = resolve(tex_for_figdir.get(d["dir"], "")), "tex"
            else:
                tgt, kind = svg, "svg"
            records.append({"src": "figure", "unit": d["dir"], "file": tgt, "kind": kind,
                            "page": fig.get("onPage"), "severity": it["severity"],
                            "category": it.get("category", "figure"),
                            "problem": f'[{rel}] {it["problem"]}', "fix": it["fix"], "round": 1})

# consistency: lifeline -> emv-dda-sequence.svg; остальное уже покрыто файлами
for f in res.get("consistency", {}).get("findings", []):
    aff = f.get("affected", [])
    theme = f.get("theme", "")
    if "lifeline" in theme.lower():
        tgt = svg_by_name.get("emv-dda-sequence.svg", "assets/figures/ch07-emv/emv-dda-sequence.svg")
        records.append({"src": "consistency", "unit": "ALL", "file": tgt, "kind": "svg",
                        "page": None, "severity": f["severity"], "category": "lifeline-consistency",
                        "problem": f["problem"] + " | affected: " + ", ".join(aff),
                        "fix": f["fix"], "round": 1})
    else:
        records.append({"src": "consistency", "unit": "ALL", "file": "(сквозное-advisory)",
                        "kind": "note", "page": None, "severity": f["severity"],
                        "category": theme, "problem": f["problem"], "fix": f["fix"], "round": 1})

r1 = [r for r in records if r["round"] == 1 and r["kind"] not in ("note", "?") and r["file"] and not r["file"].startswith("(")]
r2 = [r for r in records if r["round"] == 2]
advisory = [r for r in records if r["kind"] == "note" or r["file"].startswith("(") or r["kind"] == "?"]

by_file = defaultdict(list)
for r in r1:
    by_file[r["file"]].append(r)
plan = [{"file": f, "kind": items[0]["kind"], "items": items} for f, items in
        sorted(by_file.items(), key=lambda kv: (kv[0].split("/")[0], kv[0]))]
(ROOT / "build" / "reflow-fixplan-r1.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "build" / "reflow-r2.json").write_text(json.dumps(r2, ensure_ascii=False, indent=1), encoding="utf-8")

# ---- свежие docs/reflow ----
docs = ROOT / "docs" / "reflow"
docs.mkdir(parents=True, exist_ok=True)
for old in docs.glob("ch*.md"):
    old.unlink()
for old in docs.glob("front*.md"):
    old.unlink()
for old in docs.glob("back*.md"):
    old.unlink()

rev_by_unit = defaultdict(list)
for c in res.get("review", []):
    for f in c.get("findings", []):
        rev_by_unit[c["unit"]].append(f)
fig_by_dir = {d["dir"]: d["figures"] for d in res.get("figures", [])}
dir_for_unit = {u["key"]: u["fig_dir"] for u in manifest}

idx = ["# Типографская вычитка — свежий проход\n",
       f"Книга: {max(u['last_page'] for u in manifest)} стр. (B5), рендер 150 DPI. Свод: {len(records)} находок "
       f"({sum(1 for r in records if r['severity']=='high')} high / "
       f"{sum(1 for r in records if r['severity']=='medium')} medium / "
       f"{sum(1 for r in records if r['severity']=='low')} low). "
       f"Round-1 правок: {len(r1)} в {len(plan)} файлах; round-2 (пагинация): {len(r2)}.\n"]
for u in manifest:
    key = u["key"]
    rf = rev_by_unit.get(key, [])
    figs = fig_by_dir.get(u["fig_dir"], []) if u["fig_dir"] else []
    fig_issues = [(fg["svg"], it) for fg in figs for it in fg.get("issues", [])]
    if not rf and not fig_issues:
        continue
    idx.append(f"- [{key}]({key}.md) — текст: {len(rf)}, фигуры: {len(fig_issues)}")
    lines = [f"# {key}  (печ. стр. {u['first_page']}–{u['last_page']})\n"]
    if rf:
        lines.append("## Текст / вёрстка\n")
        for f in sorted(rf, key=lambda x: x.get("page", 0)):
            lines.append(f"- **p{f.get('page')}** `{f['severity']}/{f['category']}` — {f['problem']}\n"
                         f"  - _фикс:_ {f['fix']}  → `{f.get('target','')}`\n")
    if fig_issues:
        lines.append("## Фигуры (канон)\n")
        for svg, it in fig_issues:
            lines.append(f"- **{svg}** `{it['severity']}/{it.get('category','')}` → "
                         f"fixTarget={it.get('fixTarget')} — {it['problem']}\n  - _фикс:_ {it['fix']}\n")
    (docs / f"{key}.md").write_text("\n".join(lines), encoding="utf-8")
(docs / "_index.md").write_text("\n".join(idx), encoding="utf-8")

print(f"round-1 файлов: {len(plan)} | round-1 правок: {len(r1)} | round-2: {len(r2)} | advisory: {len(advisory)}")
print("\n== ROUND-1 план по файлам ==")
for p in plan:
    sev = Counter(i["severity"] for i in p["items"])
    print(f"  {len(p['items']):>2} [{p['kind']:9s}] {dict(sev)}  {p['file']}")
print("\n== ADVISORY / отложено автору ==")
for r in advisory:
    print(f"  [{r['severity']}/{r['category']}] {r['problem'][:90]}")
print(f"\nfiles → build/reflow-fixplan-r1.json ; round2 → build/reflow-r2.json ; docs/reflow/ refreshed")
