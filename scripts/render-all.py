#!/usr/bin/env python3
"""Рендер ВСЕХ печатных страниц книги в build/page-pngs/all/ для типографской вычитки.

Зеркалит конвенции render-chapter.py: PDF page = printed + OFFSET, имена
p{printed:03d}.png. DPI по умолчанию 150 (B5 → 1040×1477, как ждут
detect_whitespace.py и reflow-audit workflow). Чистит каталог перед рендером.

Запуск: python3 scripts/render-all.py   (RENDER_DPI=150 по умолчанию)
"""
import os
import re
import subprocess
from pathlib import Path

OFFSET = 2  # PDF page = printed page + OFFSET (front-matter pre-pages)
DPI = int(os.environ.get("RENDER_DPI", "150"))
ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "build" / "payments-book.pdf"

if not PDF.exists():
    raise SystemExit(f"{PDF} not found — run `make pdf` first")

info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True, check=True).stdout
total = int(re.search(r"Pages:\s+(\d+)", info).group(1))
last_printed = total - OFFSET

out_dir = ROOT / "build" / "page-pngs" / "all"
out_dir.mkdir(parents=True, exist_ok=True)
for old in out_dir.glob("*.png"):
    old.unlink()

for printed in range(1, last_printed + 1):
    pdf_page = printed + OFFSET
    stem = f"p{printed:03d}"
    subprocess.run(
        ["pdftoppm", "-r", str(DPI), "-f", str(pdf_page), "-l", str(pdf_page),
         str(PDF), str(out_dir / stem), "-png"],
        check=True, stdout=subprocess.DEVNULL,
    )
    cands = list(out_dir.glob(f"{stem}-*.png"))
    if cands:
        cands[0].rename(out_dir / f"{stem}.png")

print(f"rendered {last_printed} pages (p001–p{last_printed:03d}) @ {DPI} DPI → {out_dir.relative_to(ROOT)}")
