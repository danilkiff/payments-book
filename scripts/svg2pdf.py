#!/usr/bin/env python3
"""Конвертирует все SVG из assets/figures/ в PDF для включения через pdflatex.

Запускать: python3 scripts/svg2pdf.py  (или make svg)
Запускать после сохранения новых SVG-фигур из Excalidraw, перед make pdf.
Сгенерированные PDF попадают под *.pdf в .gitignore (не коммитятся).
"""
import sys
from pathlib import Path

try:
    import cairosvg
except ImportError:
    print("cairosvg не установлен. Установить: pip3 install cairosvg", file=sys.stderr)
    sys.exit(1)

root = Path(__file__).resolve().parent.parent / "assets" / "figures"
svgs = sorted(root.rglob("*.svg"))

if not svgs:
    print("SVG-файлы не найдены в assets/figures/")
    sys.exit(0)

for svg in svgs:
    pdf = svg.with_suffix(".pdf")
    cairosvg.svg2pdf(url=svg.as_uri(), write_to=str(pdf))
    print(f"  {svg.relative_to(root.parent.parent)} -> {pdf.name}")

print(f"Конвертировано: {len(svgs)} файл(ов).")
