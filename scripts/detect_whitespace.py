#!/usr/bin/env python3
"""Детектор «пустых мест» на отрендеренных страницах (PIL).
Меряет нижний провал и крупнейший внутренний разрыв в текстовом блоке.
Кросс-ссылка с манифестом: страницы-концы глав (штатно короткие) помечаются.
Печатает кандидатов; ничего не правит."""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PNG = ROOT / "build" / "page-pngs" / "all"
manifest = json.loads((ROOT / "build" / "reflow-manifest.json").read_text(encoding="utf-8"))

# границы текстового блока в пикселях (рендер 1040x1477, B5) — с запасом
X0, X1 = 90, 950
Y0, Y1 = 95, 1395          # исключаем колонтитул сверху и фолио снизу
INK_DARK = 130             # пиксель «тёмный», если <130 (0..255)
ROW_MIN_INK = 6            # строка несёт «чернила», если тёмных пикселей >= 6

chap_last = {u["last_page"]: u["key"] for u in manifest if u["num"] and u["num"] < 100}
chap_first = {u["first_page"]: u["key"] for u in manifest}


def analyze(path):
    im = Image.open(path).convert("L")
    W, H = im.size
    px = im.load()
    x1 = min(X1, W); y1 = min(Y1, H)
    ink_rows = []
    for y in range(Y0, y1):
        c = 0
        for x in range(X0, x1, 2):       # шаг 2 — быстрее, достаточно
            if px[x, y] < INK_DARK:
                c += 1
                if c >= ROW_MIN_INK:
                    break
        ink_rows.append(c >= ROW_MIN_INK)
    if not any(ink_rows):
        return {"empty_page": True, "bottom_frac": 1.0, "gap_frac": 0.0,
                "first": None, "last": None}
    n = len(ink_rows)
    first = next(i for i in range(n) if ink_rows[i])
    last = next(i for i in range(n - 1, -1, -1) if ink_rows[i])
    bottom_frac = (n - 1 - last) / n
    # крупнейший внутренний разрыв (между first и last)
    gap = run = 0
    for i in range(first, last + 1):
        if not ink_rows[i]:
            run += 1; gap = max(gap, run)
        else:
            run = 0
    gap_frac = gap / n
    return {"empty_page": False, "bottom_frac": round(bottom_frac, 3),
            "gap_frac": round(gap_frac, 3), "first": first, "last": last}


rows = []
for f in sorted(PNG.glob("p*.png")):
    p = int(f.stem[1:])
    a = analyze(f)
    rows.append((p, a))

BOTTOM_TH = 0.20
GAP_TH = 0.11
print(f"страниц: {len(rows)}  пороги: bottom>{BOTTOM_TH} gap>{GAP_TH}\n")
print("== КАНДИДАТЫ: внутренний разрыв (дыра в середине полосы) ==")
for p, a in rows:
    if a["gap_frac"] > GAP_TH and not a["empty_page"]:
        print(f"  p{p}: gap={a['gap_frac']}  bottom={a['bottom_frac']}")
print("\n== КАНДИДАТЫ: нижний провал (исключая концы глав) ==")
for p, a in rows:
    if a["bottom_frac"] > BOTTOM_TH and not a["empty_page"]:
        tag = ""
        if p in chap_last: tag = f" [конец главы {chap_last[p]} — штатно]"
        elif p + 1 in chap_first: tag = f" [перед началом {chap_first[p+1]} — возможно штатно]"
        print(f"  p{p}: bottom={a['bottom_frac']}  gap={a['gap_frac']}{tag}")
print("\n== пустые/почти пустые страницы ==")
for p, a in rows:
    if a["empty_page"] or (a["last"] is not None and a["last"] - (a["first"] or 0) < 80):
        print(f"  p{p}: {'EMPTY' if a['empty_page'] else 'почти пустая'}")

# сохранить для воркфлоу-верификации
cand = sorted({p for p, a in rows if not a["empty_page"] and
               (a["bottom_frac"] > BOTTOM_TH or a["gap_frac"] > GAP_TH)
               and p not in chap_last})
(ROOT / "build" / "whitespace-candidates.json").write_text(json.dumps(cand), encoding="utf-8")
print(f"\nкандидатов (без концов глав) → {len(cand)}: {cand}")
