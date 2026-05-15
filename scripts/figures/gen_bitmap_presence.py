"""Генератор bitmap-presence.svg для гл. 5 ISO 8583 § 5.3.

8 рядов (по байту primary bitmap MTI 0100) × 8 ячеек (биты MSB->LSB).
Заполненные ячейки -- присутствующие DE; пустые -- отсутствующие.
Бит 1 первого байта -- флаг расширения (secondary bitmap), здесь 0.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, SOFT, ACCENT_A,
  figures_dir, t, write_svg, svg_header,
)

BITMAP_HEX = "72 3C 04 81 20 C0 80 00"
bitmap = bytes.fromhex(BITMAP_HEX.replace(" ", ""))

VIEW_W = 480
VIEW_H = 290
CELL_W = 42
CELL_H = 30
GRID_X = 78
GRID_Y = 36
COL_HEADER_Y = 24

lines = svg_header(VIEW_W, VIEW_H)

# Заголовки колонок: позиции битов 1..8 (1 = MSB)
for col in range(8):
  cx = GRID_X + col * CELL_W + CELL_W / 2
  lines.append(t(cx, COL_HEADER_Y, str(col + 1), size=10, fill=MUTED, weight="bold"))

lines.append(t(GRID_X - 8, COL_HEADER_Y, "Hex", size=10, fill=MUTED, weight="bold", anchor="end"))

# Ряды: один на байт bitmap
for row in range(8):
  byte = bitmap[row]
  row_y = GRID_Y + row * CELL_H
  lines.append(t(GRID_X - 8, row_y + 19, f"{byte:02X}", size=11, fill=INK,
                 anchor="end", weight="bold"))

  for col in range(8):
    bit_pos = row * 8 + col + 1
    is_set = bool(byte & (1 << (7 - col)))
    cx = GRID_X + col * CELL_W
    cy = row_y

    if is_set:
      fill, opacity = ACCENT_A, 0.20
      text_content = f"DE {bit_pos}" if bit_pos >= 2 else "+64"
      text_weight = "bold"
    else:
      fill, opacity = SOFT, 1.0
      text_content = ""
      text_weight = "normal"

    lines.append(
      f'<rect x="{cx}" y="{cy}" width="{CELL_W - 1}" height="{CELL_H - 1}" '
      f'fill="{fill}" fill-opacity="{opacity}" '
      f'stroke="{MUTED}" stroke-width="0.5"/>'
    )
    if text_content:
      font_size = 10 if len(text_content) <= 4 else 9
      lines.append(t(cx + CELL_W / 2, cy + 19, text_content,
                     size=font_size, fill=INK, weight=text_weight))

lines.append("</svg>")

write_svg(figures_dir() / "ch06-iso8583" / "bitmap-presence.svg", lines)
