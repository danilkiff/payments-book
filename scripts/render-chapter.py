#!/usr/bin/env python3
"""Перерендер PNG для одной главы после правок вёрстки.

Парсит build/payments-book.aux: находит первую страницу главы и первую
страницу следующего «якоря» (главы/эпилога/карты первоисточников),
рендерит pdftoppm'ом в build/page-pngs/<chXX>/.

Запуск: python3 scripts/render-chapter.py ch07
"""

import os
import re
import subprocess
import sys
from pathlib import Path

OFFSET = 2  # PDF page = printed page + OFFSET (front-matter pre-pages)
DPI = int(os.environ.get("RENDER_DPI", "110"))  # 150 даёт ~1040×1477 — предел до даунскейла
ROOT = Path(__file__).resolve().parent.parent
AUX = ROOT / "build" / "payments-book.aux"
PDF = ROOT / "build" / "payments-book.pdf"

if len(sys.argv) != 2 or not re.fullmatch(r"ch\d{2}", sys.argv[1]):
    sys.exit("usage: render-chapter.py chNN  (e.g., ch07)")
ch_id = sys.argv[1]
chn = int(ch_id[2:])

if not AUX.exists():
    sys.exit(f"{AUX} not found — run `make pdf` first")

pattern = re.compile(r"\\newlabel\{ch:[a-z0-9-]+\}\{\{([0-9.]+)\}\{([0-9]+)\}")
labels: list[tuple[int, str]] = []  # (printed_page, number)
for line in AUX.read_text(encoding="utf-8", errors="ignore").splitlines():
    m = pattern.search(line)
    if m:
        labels.append((int(m.group(2)), m.group(1)))
labels.sort()

current = next((p for p, num in labels if num == str(chn)), None)
if current is None:
    sys.exit(f"chapter {chn} not found in {AUX}")

next_page = next((p for p, _ in labels if p > current), None)
if next_page is None:
    info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True, check=True).stdout
    total = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    last_printed = total - OFFSET
else:
    last_printed = next_page - 1

out_dir = ROOT / "build" / "page-pngs" / ch_id
out_dir.mkdir(parents=True, exist_ok=True)
for old in out_dir.glob("*.png"):
    old.unlink()

for printed in range(current, last_printed + 1):
    pdf_page = printed + OFFSET
    subprocess.run(
        [
            "pdftoppm",
            "-r", str(DPI),
            "-f", str(pdf_page),
            "-l", str(pdf_page),
            str(PDF),
            str(out_dir / f"p{printed}"),
            "-png",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    candidates = list(out_dir.glob(f"p{printed}-*.png"))
    if candidates:
        candidates[0].rename(out_dir / f"p{printed}.png")

n = last_printed - current + 1
print(f"{ch_id}: rendered {n} pages (p{current}–p{last_printed}) into {out_dir.relative_to(ROOT)}")
