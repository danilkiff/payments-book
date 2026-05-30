#!/usr/bin/env python3
"""Строгий детектор полировки полос (round-2 пагинации).

Жёстче detect_whitespace.py: ловит нижние недоборы, внутренние разрывы и
почти-пустые полосы при меньших порогах. Исключает штатные концы/начала глав
(по манифесту). Для каждой полосы-кандидата печатает главу и тип дефекта.
Одиночные строки-абзацы и заголовки-сироты проявляются как нижний зазор
полосы-предшественницы и попадают в выборку через него.

Вход: build/page-pngs/all/p*.png + build/reflow-manifest.json
Выход: build/polish-candidates.json + ранжированная сводка.
"""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PNG = ROOT / "build" / "page-pngs" / "all"
manifest = json.loads((ROOT / "build" / "reflow-manifest.json").read_text(encoding="utf-8"))

X0, X1 = 90, 950
Y0, Y1 = 95, 1395
INK_DARK = 130
ROW_MIN_INK = 6

# пороги жёстче detect_whitespace (0.20 / 0.11)
BOTTOM_TH = 0.13   # ~7 строк недобора внизу
GAP_TH = 0.085     # ~4 строки внутренней дыры
NEAR_EMPTY = 0.55  # ink-span < 55% блока

chap_last = {u["last_page"]: u["key"] for u in manifest if u["num"] and u["num"] < 100}
chap_first = {u["first_page"]: u["key"] for u in manifest}
# страница -> ключ главы (по диапазонам)
page_chapter = {}
for u in manifest:
    for p in range(u["first_page"], u["last_page"] + 1):
        page_chapter[p] = u["key"]


def analyze(path):
    im = Image.open(path).convert("L")
    W, H = im.size
    px = im.load()
    x1 = min(X1, W); y1 = min(Y1, H)
    ink_rows = []
    for y in range(Y0, y1):
        c = 0
        for x in range(X0, x1, 2):
            if px[x, y] < INK_DARK:
                c += 1
                if c >= ROW_MIN_INK:
                    break
        ink_rows.append(c >= ROW_MIN_INK)
    n = len(ink_rows)
    if not any(ink_rows):
        return {"empty": True, "bottom": 1.0, "gap": 0.0, "span": 0.0}
    first = next(i for i in range(n) if ink_rows[i])
    last = next(i for i in range(n - 1, -1, -1) if ink_rows[i])
    bottom = (n - 1 - last) / n
    gap = run = 0
    for i in range(first, last + 1):
        if not ink_rows[i]:
            run += 1; gap = max(gap, run)
        else:
            run = 0
    return {"empty": False, "bottom": round(bottom, 3),
            "gap": round(gap / n, 3), "span": round((last - first) / n, 3)}


rows = []
for f in sorted(PNG.glob("p*.png")):
    p = int(f.stem[1:])
    rows.append((p, analyze(f)))

cands = []
for p, a in rows:
    if a["empty"]:
        if p not in chap_last:
            cands.append((p, "EMPTY", a))
        continue
    kinds = []
    if a["bottom"] > BOTTOM_TH and p not in chap_last and (p + 1) not in chap_first:
        kinds.append("bottom-void")
    if a["gap"] > GAP_TH:
        kinds.append("internal-gap")
    if a["span"] < NEAR_EMPTY and p not in chap_last and p not in chap_first:
        kinds.append("near-empty")
    if kinds:
        cands.append((p, "+".join(kinds), a))

# ранжируем по «тяжести»: max(bottom, gap, 1-span)
def sev(a):
    return max(a["bottom"], a["gap"], (1 - a["span"]) if not a["empty"] else 1.0)

cands.sort(key=lambda c: -sev(c[2]))

print(f"страниц: {len(rows)}  пороги: bottom>{BOTTOM_TH} gap>{GAP_TH} span<{NEAR_EMPTY}")
print(f"кандидатов: {len(cands)}\n")
print(f"{'стр':>4}  {'severity':>8}  {'тип':<28} {'bottom/gap/span':<20} глава")
for p, kind, a in cands:
    m = f"{a['bottom']}/{a['gap']}/{a['span']}"
    print(f"p{p:<4} {sev(a):8.2f}  {kind:<28} {m:<20} {page_chapter.get(p,'?')}")

out = [{"page": p, "kind": kind, **a, "chapter": page_chapter.get(p)} for p, kind, a in cands]
(ROOT / "build" / "polish-candidates.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n→ build/polish-candidates.json ({len(cands)} полос)")
