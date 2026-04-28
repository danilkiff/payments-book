#!/usr/bin/env python3
"""Конвертирует все SVG из assets/figures/ в PDF для включения через pdflatex.

Запускать: python3 scripts/svg2pdf.py  (или make svg)
Запускать после сохранения новых SVG-фигур из Excalidraw, перед make pdf.
Сгенерированные PDF попадают под *.pdf в .gitignore (не коммитятся).

Использует rsvg-convert (librsvg) — в отличие от cairosvg, корректно
рендерит unicode-стрелки (→, ⇒, …) с системными fallback-шрифтами.
Установка: brew install librsvg
"""
import shutil
import subprocess
import sys
from pathlib import Path

if shutil.which("rsvg-convert") is None:
    print("rsvg-convert не установлен. Установить: brew install librsvg", file=sys.stderr)
    sys.exit(1)

root = Path(__file__).resolve().parent.parent / "assets" / "figures"
svgs = sorted(root.rglob("*.svg"))

if not svgs:
    print("SVG-файлы не найдены в assets/figures/")
    sys.exit(0)

errors = 0
for svg in svgs:
    pdf = svg.with_suffix(".pdf")
    res = subprocess.run(
        ["rsvg-convert", "-f", "pdf", "-o", str(pdf), str(svg)],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        errors += 1
        print(f"  ERROR {svg.relative_to(root.parent.parent)}: {res.stderr.strip()}", file=sys.stderr)
        continue
    print(f"  {svg.relative_to(root.parent.parent)} -> {pdf.name}")

print(f"Конвертировано: {len(svgs) - errors} / {len(svgs)} файл(ов).")
sys.exit(1 if errors else 0)
