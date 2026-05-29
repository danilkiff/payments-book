"""Генератор cid-anatomy.svg для гл. 7 EMV (GENERATE AC: запрос и ответ).

P1 команды GENERATE AC задаёт, какую криптограмму терминал запрашивает
(биты 8--7: тип; бит 6: запросить CDA). CID (Cryptogram Information Data,
тег 9F27) в ответе сообщает фактически выданный тип (биты 8--7), признак
advice (бит 4) и код причины (биты 3--1).
Пример: P1 = 0xA0 (запрос ARQC + CDA), CID = 0x80 (карта вернула ARQC).
Источник: emvco-book3, §6.5.5 и Table 14.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, SOFT, ACCENT_A, WARN,
  figures_dir, t, write_svg, svg_header,
)

LABELS = {
  (0, 8): "тип", (0, 6): "CDA",
  (1, 8): "тип", (1, 4): "advice", (1, 3): "причина",
}
DEFINED = {
  (0, 8), (0, 7), (0, 6),
  (1, 8), (1, 7), (1, 4), (1, 3), (1, 2), (1, 1),
}
BYTE_NAMES = ["P1: запрос", "CID 9F27: ответ"]
EXAMPLE_HEX = [0xA0, 0x80]

VIEW_W = 700
CELL_W = 70
CELL_H = 30
LABEL_W = 120
HEADER_H = 26
GRID_X = LABEL_W + 6
GRID_Y = HEADER_H + 10
NUM_ROWS = 2
NUM_COLS = 8

HEX_BAR_Y = GRID_Y + NUM_ROWS * CELL_H + 18
HEX_BAR_H = 42
VIEW_H = HEX_BAR_Y + HEX_BAR_H + 8

lines = svg_header(VIEW_W, VIEW_H)

lines.append(t(LABEL_W - 6, HEADER_H - 4, "Байт", size=10, fill=MUTED,
               weight="bold", anchor="end"))
for col in range(NUM_COLS):
  bit_pos = 8 - col
  cx = GRID_X + col * CELL_W + CELL_W / 2
  if col == 0:
    label = f"бит {bit_pos} (MSB)"
  elif col == NUM_COLS - 1:
    label = f"бит {bit_pos} (LSB)"
  else:
    label = f"бит {bit_pos}"
  lines.append(t(cx, HEADER_H - 4, label, size=10, fill=MUTED, weight="bold"))

for row in range(NUM_ROWS):
  ry = GRID_Y + row * CELL_H
  lines.append(t(LABEL_W - 6, ry + 19, BYTE_NAMES[row], size=10, fill=INK,
                 weight="bold", anchor="end"))
  for col in range(NUM_COLS):
    bit_pos = 8 - col
    cx = GRID_X + col * CELL_W
    is_defined = (row, bit_pos) in DEFINED
    bit_value = (EXAMPLE_HEX[row] >> (bit_pos - 1)) & 1
    is_set = is_defined and bit_value == 1
    if is_set:
      fill, opacity, weight = WARN, 0.18, "bold"
    elif is_defined:
      fill, opacity, weight = ACCENT_A, 0.15, "normal"
    else:
      fill, opacity, weight = SOFT, 1.0, "normal"
    lines.append(
      f'<rect x="{cx}" y="{ry}" width="{CELL_W - 1}" height="{CELL_H - 1}" '
      f'fill="{fill}" fill-opacity="{opacity}" stroke="{MUTED}" stroke-width="0.5"/>'
    )
    label = LABELS.get((row, bit_pos))
    if label:
      lines.append(t(cx + CELL_W / 2, ry + 19, label, size=10, fill=INK, weight=weight))

lines.append(t(LABEL_W - 6, HEX_BAR_Y + 16, "Пример:", size=10, fill=MUTED,
               weight="bold", anchor="end"))
for col in range(NUM_ROWS):
  cx = GRID_X + col * (CELL_W * NUM_COLS / NUM_ROWS)
  box_w = CELL_W * NUM_COLS / NUM_ROWS - 4
  byte = EXAMPLE_HEX[col]
  has_set = any((col, b) in DEFINED and (byte >> (b - 1)) & 1 for b in range(1, 9))
  fill = WARN if has_set else SOFT
  lines.append(
    f'<rect x="{cx}" y="{HEX_BAR_Y}" width="{box_w}" height="{HEX_BAR_H}" '
    f'fill="{fill}" fill-opacity="0.18" stroke="{MUTED}" stroke-width="0.5"/>'
  )
  meaning = "запрос ARQC + CDA" if col == 0 else "карта вернула ARQC"
  lines.append(t(cx + box_w / 2, HEX_BAR_Y + 17, f"0x{byte:02X}", size=11,
                 fill=INK, weight="bold"))
  lines.append(t(cx + box_w / 2, HEX_BAR_Y + 33, meaning, size=9, fill=MUTED))

lines.append("</svg>")
write_svg(figures_dir() / "ch07-emv" / "cid-anatomy.svg", lines)
