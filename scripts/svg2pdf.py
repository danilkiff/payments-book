#!/usr/bin/env python3
"""Конвертирует SVG из assets/figures/ в PDF через Inkscape headless.

Использует Inkscape --shell (один процесс на весь батч), чтобы избежать
~1-2 с стартапа на каждый из ~70 файлов.

Запускать: python3 scripts/svg2pdf.py  (или make svg)
Установка Inkscape: brew install inkscape (macOS) / apt install inkscape (Ubuntu).
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

INKSCAPE = "inkscape"

if shutil.which(INKSCAPE) is None:
    print("inkscape не установлен. Установить: brew install inkscape", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent / "assets" / "figures"
REPO = ROOT.parent.parent


sources = sorted(ROOT.rglob("*.svg"))

if not sources:
    print("SVG-файлы не найдены в assets/figures/")
    sys.exit(0)

jobs: list[tuple[Path, Path]] = [(src, src.with_suffix(".pdf")) for src in sources]

shell_lines = [
    f"file-open:{src}; export-filename:{pdf}; export-type:pdf; export-do; file-close"
    for src, pdf in jobs
]
shell_lines.append("quit")
shell_input = "\n".join(shell_lines) + "\n"

start = time.time()
result = subprocess.run(
    [INKSCAPE, "--shell"],
    input=shell_input,
    capture_output=True,
    text=True,
)

errors = 0
for src, pdf in jobs:
    rel = src.relative_to(REPO)
    if pdf.exists() and pdf.stat().st_size > 0 and pdf.stat().st_mtime >= start:
        print(f"  {rel} -> {pdf.name}")
    else:
        errors += 1
        print(f"  ERROR {rel}: PDF не создан или пуст", file=sys.stderr)

if errors:
    print("--- inkscape stderr (хвост) ---", file=sys.stderr)
    for line in result.stderr.splitlines()[-40:]:
        print(line, file=sys.stderr)

print(f"Конвертировано: {len(jobs) - errors} / {len(jobs)} файл(ов).")
sys.exit(1 if errors else 0)
