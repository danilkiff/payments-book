#!/usr/bin/env python3
"""Свод находок аудита вёрстки в план правок, сгруппированный по файлам.

Вход: build/reflow-audit-result.json (review/figures/consistency) + манифест.
Выход: build/reflow-fix-plan.json (по файлам) + печать сводки и плана.
Классифицирует round1 (структурные/локальные, применяем сразу) vs round2
(координатная подгонка пагинации — после пересборки/перерендера).
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
res = json.loads((ROOT / "build" / "reflow-audit-result.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "build" / "reflow-manifest.json").read_text(encoding="utf-8"))

# svg(rel "dir/name") -> generator script
gen_for_svg = {}
pat = re.compile(r'figures_dir\(\)\s*/\s*"([^"]+)"\s*/\s*"([^"]+\.svg)"')
for g in (ROOT / "scripts" / "figures").glob("gen_*.py"):
    for m in pat.finditer(g.read_text(encoding="utf-8", errors="ignore")):
        gen_for_svg[f"{m.group(1)}/{m.group(2)}"] = f"scripts/figures/{g.name}"

# figDir -> tex
tex_for_figdir = {u["fig_dir"]: u["tex"] for u in manifest if u["fig_dir"]}


def norm_path(p):
    if not p:
        return ""
    p = p.strip().strip("`")
    # отрезать возможный префикс /Users/...
    i = p.find("assets/")
    if i < 0:
        i = p.find("src/")
    if i < 0:
        i = p.find("scripts/")
    if i > 0:
        p = p[i:]
    return p


ROUND2_KW = re.compile(r"looseness|needspace|enlargethispage|подтян|сжать|reflow|переформул|"
                       r"висяч|короткий хвост|обрубок|на одну строку|сэконом")
PAGINATION_CATS = {"whitespace", "pagebreak", "widow-orphan", "underfull", "overfull", "heading-position"}


def classify_round(cat, fix):
    fix = fix or ""
    if cat in PAGINATION_CATS:
        # структурный фикс плэйсмента флоата — round1; координатная подгонка — round2
        if re.search(r"\[H\]|htbp|tbp|placement|float|размещени|\[!?ht", fix) and not ROUND2_KW.search(fix):
            return 1
        if ROUND2_KW.search(fix):
            return 2
        return 2  # по умолчанию пагинация — round2 (после пересборки)
    return 1


records = []  # unified

# --- review ---
for c in res.get("review", []):
    for f in c.get("findings", []):
        tgt = norm_path(f.get("target", ""))
        kind = ("generator" if tgt.startswith("scripts/figures/")
                else "svg" if tgt.endswith(".svg")
                else "tex" if tgt.endswith(".tex") else "?")
        # generated svg, но указан .svg → перенаправить на генератор
        if kind == "svg":
            rel = "/".join(Path(tgt).parts[-2:])
            if rel in gen_for_svg:
                tgt, kind = gen_for_svg[rel], "generator"
        records.append({
            "src": "review", "unit": c["unit"], "file": tgt, "kind": kind,
            "page": f.get("page"), "severity": f["severity"], "category": f["category"],
            "problem": f["problem"], "fix": f["fix"],
            "round": classify_round(f["category"], f["fix"]),
        })

# --- figures ---
for d in res.get("figures", []):
    for fig in d.get("figures", []):
        svg = norm_path(fig.get("svg", ""))
        rel = "/".join(Path(svg).parts[-2:]) if svg else ""
        for it in fig.get("issues", []):
            ft = it.get("fixTarget", "svg")
            if ft == "generator" or rel in gen_for_svg:
                tgt = gen_for_svg.get(rel, svg)
                kind = "generator"
            elif ft == "tex":
                tgt = tex_for_figdir.get(d["dir"], "")
                kind = "tex"
            else:
                tgt, kind = svg, "svg"
            records.append({
                "src": "figure", "unit": d["dir"], "file": norm_path(tgt), "kind": kind,
                "page": fig.get("onPage"), "severity": it["severity"], "category": it.get("category", "figure"),
                "problem": f'[{rel}] {it["problem"]}', "fix": it["fix"],
                "round": 1,  # фигурные правки не двигают пагинацию (box фиксирован)
            })

# --- consistency ---
for f in res.get("consistency", {}).get("findings", []):
    records.append({
        "src": "consistency", "unit": "ALL", "file": "(сквозное)", "kind": "multi",
        "page": None, "severity": f["severity"], "category": f.get("theme", "consistency"),
        "problem": f["problem"] + " | affected: " + ", ".join(f.get("affected", [])),
        "fix": f["fix"], "round": 1,
    })

# ---- сводка ----
print(f"ВСЕГО находок: {len(records)}  (review={sum(1 for r in records if r['src']=='review')}, "
      f"figure={sum(1 for r in records if r['src']=='figure')}, "
      f"consistency={sum(1 for r in records if r['src']=='consistency')})")
print("\nПо severity:", dict(Counter(r["severity"] for r in records)))
print("По round:   ", dict(Counter(r["round"] for r in records)))
print("\nПо категориям:")
for cat, n in Counter(r["category"] for r in records).most_common():
    print(f"  {n:>3}  {cat}")

# группировка по файлам
by_file = defaultdict(list)
for r in records:
    by_file[r["file"]].append(r)

print(f"\nЗатронуто файлов: {len([f for f in by_file if f and f!='(сквозное)'])}")
print("\n== HIGH severity (все) ==")
for r in records:
    if r["severity"] == "high":
        pg = f"p{r['page']}" if r["page"] else "—"
        print(f"  [{r['round']}] {r['category']:16s} {pg:>5} {r['file']}")
        print(f"        ПРОБ: {r['problem'][:170]}")
        print(f"        ФИКС: {r['fix'][:170]}")

# план по файлам
plan = []
for file, items in sorted(by_file.items(), key=lambda kv: -len(kv[1])):
    sev = Counter(i["severity"] for i in items)
    rounds = sorted(set(i["round"] for i in items))
    plan.append({"file": file, "kind": items[0]["kind"], "n": len(items),
                 "severity": dict(sev), "rounds": rounds,
                 "items": [{"page": i["page"], "severity": i["severity"], "category": i["category"],
                            "round": i["round"], "problem": i["problem"], "fix": i["fix"]} for i in items]})
(ROOT / "build" / "reflow-fix-plan.json").write_text(
    json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")

print("\n== Файлы по числу находок (kind | n | severity | rounds) ==")
for p in plan:
    print(f"  {p['n']:>2}  [{p['kind']:9s}] r{p['rounds']} {dict(p['severity'])}  {p['file']}")
print("\nплан → build/reflow-fix-plan.json")
