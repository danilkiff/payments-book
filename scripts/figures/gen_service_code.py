"""Генератор service-code.svg для гл. 3 § "Сервисный код".

Три позиции сервисного кода Track 2 (ISO/IEC 7813:2006 Table 3).
Каждая позиция действует независимо. Жёлтым подсвечены значения примера
201 из дампа MTI 0100 (гл. 5).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, SOFT, WARN,
  figures_dir, t, write_svg, svg_header,
)

POS_1 = [
  ("1", "международная"),
  ("2", "международная + чип"),
  ("5", "национальная"),
  ("6", "национальная + чип"),
  ("7", "частная"),
  ("9", "тестовая"),
]
POS_2 = [
  ("0", "обычная"),
  ("2", "онлайн через эмитента"),
  ("4", "через эмитента, если нет соглашения"),
]
POS_3 = [
  ("0", "без огр., PIN"),
  ("1", "без ограничений"),
  ("2", "товары/услуги"),
  ("3", "ATM, PIN"),
  ("4", "только наличные"),
  ("5", "товары/услуги, PIN"),
  ("6", "без огр., PIN при наличии PED"),
  ("7", "товары/услуги, PIN при PED"),
]

EXAMPLE = ("2", "0", "1")

POSITIONS = [
  ("Позиция 1", "интерчейндж + чип", POS_1, EXAMPLE[0]),
  ("Позиция 2", "авторизация", POS_2, EXAMPLE[1]),
  ("Позиция 3", "услуги + PIN", POS_3, EXAMPLE[2]),
]

VIEW_W = 720
COL_W = 230
COL_GAP = 12
COL_X = [10, 10 + COL_W + COL_GAP, 10 + 2 * (COL_W + COL_GAP)]
HEADER_H = 50
EXAMPLE_BAR_H = 50
ROW_H = 20
NUM_ROWS_MAX = max(len(p[2]) for p in POSITIONS)

VIEW_H = HEADER_H + EXAMPLE_BAR_H + (NUM_ROWS_MAX + 1) * ROW_H + 10

lines = svg_header(VIEW_W, VIEW_H)

for col_idx, (title, subtitle, values, example_value) in enumerate(POSITIONS):
  x = COL_X[col_idx]
  cx = x + COL_W / 2

  lines.append(t(cx, 18, title, size=11, fill=MUTED, weight="bold"))
  lines.append(t(cx, 34, subtitle, size=10, fill=MUTED))

  example_cell_y = HEADER_H
  cell_w = 60
  cell_x = cx - cell_w / 2
  lines.append(
    f'<rect x="{cell_x}" y="{example_cell_y}" width="{cell_w}" '
    f'height="{EXAMPLE_BAR_H - 8}" rx="4" '
    f'fill="{WARN}" fill-opacity="0.40" '
    f'stroke="{WARN}" stroke-width="1.5"/>'
  )
  lines.append(t(cx, example_cell_y + 30, example_value, size=24, fill=INK, weight="bold"))

  rows_start_y = HEADER_H + EXAMPLE_BAR_H + 14
  lines.append(t(x + 14, rows_start_y, "Значение", size=9, fill=MUTED, weight="bold", anchor="start"))
  lines.append(t(x + 60, rows_start_y, "Смысл", size=9, fill=MUTED, weight="bold", anchor="start"))

  for row_idx, (val, meaning) in enumerate(values):
    row_y = rows_start_y + 6 + (row_idx + 1) * ROW_H
    is_example = (val == example_value)

    if is_example:
      lines.append(
        f'<rect x="{x}" y="{row_y - 14}" width="{COL_W}" '
        f'height="{ROW_H}" fill="{WARN}" fill-opacity="0.25"/>'
      )

    lines.append(t(x + 18, row_y, val, size=11, fill=INK,
                   weight="bold" if is_example else "normal"))
    font_size = 10 if len(meaning) <= 26 else 9
    lines.append(t(x + 36, row_y, meaning, size=font_size, fill=INK,
                   weight="bold" if is_example else "normal", anchor="start"))

lines.append("</svg>")

write_svg(figures_dir() / "ch04-card-data" / "service-code.svg", lines)
