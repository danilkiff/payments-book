#!/usr/bin/env python3
"""Конвертирует SVG из assets/figures/ в PDF через Inkscape headless.

Инкрементально: пропускает PDF, который не старше своего SVG. Для полной
пересборки — `make clean && make pdf` (удаляет PDF, дальше всё с нуля).

Использует Inkscape --shell (один процесс на весь батч), чтобы избежать
~1-2 с стартапа на каждый файл.

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
    print(
        "inkscape не установлен. "
        "Установить: brew install inkscape (macOS) / apt install inkscape (Ubuntu)",
        file=sys.stderr,
    )
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent / "assets" / "figures"
REPO = ROOT.parent.parent


def is_stale(src: Path, pdf: Path) -> bool:
    if not pdf.exists():
        return True
    st = pdf.stat()
    if st.st_size == 0:
        return True
    return st.st_mtime < src.stat().st_mtime


sources = sorted(ROOT.rglob("*.svg"))

if not sources:
    print("SVG-файлы не найдены в assets/figures/")
    sys.exit(0)

jobs: list[tuple[Path, Path]] = []
for src in sources:
    pdf = src.with_suffix(".pdf")
    if is_stale(src, pdf):
        jobs.append((src, pdf))

skipped = len(sources) - len(jobs)

if not jobs:
    print(f"Все {len(sources)} PDF актуальны (PDF не старше SVG).")
    sys.exit(0)

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

converted = len(jobs) - errors
summary = f"Конвертировано: {converted} / {len(jobs)}"
if skipped:
    summary += f" (пропущено актуальных: {skipped})"
summary += "."
print(summary)
sys.exit(1 if errors else 0)
