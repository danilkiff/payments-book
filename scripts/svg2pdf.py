#!/usr/bin/env python3
"""Конвертирует SVG из assets/figures/ в PDF через Inkscape headless.

Поддерживает оба формата исходников:
- *.svg          — Inkscape native (новый канон, коммитится)
- *.gen.svg      — транзиентный продукт excalidraw2svg.py (gitignore)

Если для одного базнейма найдены оба .svg и .gen.svg, скрипт ругается:
после миграции фигуры .excalidraw должен быть удалён, иначе старая
сгенерированная версия будет затирать ручные правки в Inkscape-исходнике.

Использует Inkscape --shell (один процесс на весь батч), чтобы избежать
~1-2 с стартапа на каждый из 79 файлов.

Запускать: python3 scripts/svg2pdf.py  (или make svg)
Установка Inkscape: brew install inkscape (macOS) / apt install inkscape (Ubuntu).
"""
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

INKSCAPE = "inkscape"

if shutil.which(INKSCAPE) is None:
    print("inkscape не установлен. Установить: brew install inkscape", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent / "assets" / "figures"
REPO = ROOT.parent.parent


def base_of(svg: Path) -> Path:
    """Канонический базнейм без любого из расширений (.svg или .gen.svg)."""
    if svg.name.endswith(".gen.svg"):
        return svg.with_name(svg.name[: -len(".gen.svg")])
    return svg.with_suffix("")


sources: dict[Path, list[Path]] = defaultdict(list)
for svg in sorted(ROOT.rglob("*.svg")):
    sources[base_of(svg)].append(svg)

if not sources:
    print("SVG-файлы не найдены в assets/figures/")
    sys.exit(0)

collisions = {b: paths for b, paths in sources.items() if len(paths) > 1}
if collisions:
    print("ERROR: найдены оба .svg и .gen.svg для одного базнейма:", file=sys.stderr)
    print("Удалите .excalidraw (и .gen.svg) после миграции в Inkscape.", file=sys.stderr)
    for base, paths in sorted(collisions.items()):
        print(f"  базнейм {base.relative_to(REPO)}:", file=sys.stderr)
        for p in paths:
            print(f"    {p.relative_to(REPO)}", file=sys.stderr)
    sys.exit(2)

jobs: list[tuple[Path, Path]] = []
for base, paths in sorted(sources.items()):
    src = paths[0]
    pdf = base.with_suffix(".pdf")
    jobs.append((src, pdf))

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
