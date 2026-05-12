#!/usr/bin/env python3
"""Перекраска SVG-фигур из палитры Excalidraw в книжную палитру (src/styles.tex).

Маппинг:
  Excalidraw HEX      → Book HEX (роль)
  #1e1e1e             → #1A2030  (Ink: текст и контуры по умолчанию)
  #4a9eed             → #4E63D9  (AccentA: нейтральный синий акцент)
  #8b5cf6             → #7759D6  (AccentB: вторичный фиолетовый акцент)
  #22c55e             → #2F8B67  (Good: успех/ок)
  #166534             → #2F8B67  (Good: тёмно-зелёный для текста)
  #f59e0b             → #B8821C  (Warn: предупреждение)
  #adb5bd             → #5C647A  (Muted: нейтральные контуры/каркас)
  #f8f9fa             → #F5F7FD  (Soft: фон панели)
  #dbe4ff (pastel)    → #4E63D9 + fill-opacity 0.15
  #e5dbff (pastel)    → #7759D6 + fill-opacity 0.15
  #d3f9d8 (pastel)    → #2F8B67 + fill-opacity 0.15
  #fff3bf (pastel)    → #B8821C + fill-opacity 0.18
  #ebfbee (pastel)    → #2F8B67 + fill-opacity 0.08

Скрипт idempotent: повторный прогон не меняет уже перекрашенные файлы.

Usage:
  python3 scripts/recolor.py path/to/figure.gen.svg [...]
  python3 scripts/recolor.py --all          # все *.gen.svg и *.svg под assets/figures/
  python3 scripts/recolor.py --dry-run ...  # показать diff, не писать
"""
import argparse
import re
import sys
from pathlib import Path

# Solid color substitutions (strokes, ink text, marker fills).
COLOR_MAP = {
    "#1e1e1e": "#1A2030",
    "#4a9eed": "#4E63D9",
    "#8b5cf6": "#7759D6",
    "#22c55e": "#2F8B67",
    "#166534": "#2F8B67",
    "#f59e0b": "#B8821C",
    "#adb5bd": "#5C647A",
    "#f8f9fa": "#F5F7FD",
}

# Pastel fill substitutions: (book_color, new_fill_opacity).
# Книжные цвета насыщеннее, чем Excalidraw-пастели,
# поэтому fill-opacity снижается, чтобы итоговая интенсивность была сравнимой.
PASTEL_FILLS = {
    "#dbe4ff": ("#4E63D9", "0.15"),
    "#e5dbff": ("#7759D6", "0.15"),
    "#d3f9d8": ("#2F8B67", "0.15"),
    "#fff3bf": ("#B8821C", "0.18"),
    "#ebfbee": ("#2F8B67", "0.08"),
}

# Regex для пары `fill="<pastel>" fill-opacity="X.XX"`.
# Сначала заменяем такие пары целиком (fill-opacity перекалибровывается),
# чтобы не зависеть от ранее установленного значения opacity.
PASTEL_PAIR_RE = re.compile(
    r'fill="(#(?:dbe4ff|e5dbff|d3f9d8|fff3bf|ebfbee))"\s+fill-opacity="[\d.]+"',
    re.IGNORECASE,
)

# Если pastel-fill встречается без fill-opacity (одинокий fill), добавляем явный opacity.
PASTEL_SOLO_RE = re.compile(
    r'fill="(#(?:dbe4ff|e5dbff|d3f9d8|fff3bf|ebfbee))"(?!\s*\s+fill-opacity)',
    re.IGNORECASE,
)


def recolor_text(svg: str) -> str:
    # 1. Pastel fills with explicit opacity -> book color + recalibrated opacity.
    def replace_pair(m: re.Match[str]) -> str:
        pastel = m.group(1).lower()
        book_color, opacity = PASTEL_FILLS[pastel]
        return f'fill="{book_color}" fill-opacity="{opacity}"'

    svg = PASTEL_PAIR_RE.sub(replace_pair, svg)

    # 2. Pastel fills without opacity -> book color + default opacity.
    def replace_solo(m: re.Match[str]) -> str:
        pastel = m.group(1).lower()
        book_color, opacity = PASTEL_FILLS[pastel]
        return f'fill="{book_color}" fill-opacity="{opacity}"'

    svg = PASTEL_SOLO_RE.sub(replace_solo, svg)

    # 3. Solid color substitutions (strokes, text fills, marker definitions, url() refs).
    # Replace both lowercase and uppercase variants; book colors are uppercase so already-recolored
    # files are no-op.
    for old, new in COLOR_MAP.items():
        svg = svg.replace(old, new)
        svg = svg.replace(old.upper(), new)

    return svg


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", type=Path, help=".gen.svg или .svg для перекраски")
    parser.add_argument("--all", action="store_true", help="обработать все *.gen.svg и *.svg под assets/figures/")
    parser.add_argument("--dry-run", action="store_true", help="показать изменения, не писать")
    args = parser.parse_args()

    if args.all:
        root = Path(__file__).resolve().parent.parent / "assets" / "figures"
        paths = sorted(p for p in root.rglob("*.svg"))
    else:
        paths = args.paths

    if not paths:
        parser.error("укажите файлы или --all")

    changed = 0
    for path in paths:
        if not path.exists():
            print(f"  SKIP {path}: не существует", file=sys.stderr)
            continue
        original = path.read_text(encoding="utf-8")
        recolored = recolor_text(original)
        if recolored == original:
            print(f"  no-op {path.name}")
            continue
        changed += 1
        if args.dry_run:
            print(f"  WOULD WRITE {path.name}")
        else:
            path.write_text(recolored, encoding="utf-8")
            print(f"  {path.name}")

    print(f"Перекрашено: {changed} / {len(paths)} файл(ов).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
