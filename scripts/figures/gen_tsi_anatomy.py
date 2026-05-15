"""Генератор tsi-anatomy.svg для гл. 7 EMV.

TSI -- тег 0x9B, 2 байта битовых флагов выполненных функций в~EMV-
транзакции (counterpart TVR: TVR пишет провалы/факты проверок, TSI
пишет "что было выполнено").

Байт 1: ODA, CV, Card RM, Issuer auth, Terminal RM, Script processing.
Байт 2: весь RFU.

Пример: TSI = 0xE800 -- офлайн-транзакция, всё выполнено кроме online-этапов.
Источник: emvco-book3 Annex C7.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, SOFT, ACCENT_A, WARN,
  figures_dir, t, write_svg, svg_header,
)

LABELS = {
  (0, 8): "ODA",
  (0, 7): "CV",
  (0, 6): "Card RM",
  (0, 5): "Issuer auth",
  (0, 4): "Term RM",
  (0, 3): "Script",
}

FUNCTIONAL_BITS = set(LABELS.keys())

BYTE_NAMES = ["Байт 1", "Байт 2"]

# Пример: TSI = 0xE800 -- offline транзакция:
# ODA (бит 8), CV (бит 7), Card RM (бит 6), Term RM (бит 4) выполнены;
# Issuer auth и Script не выполнены (нет онлайна).
EXAMPLE_HEX = [0xE8, 0x00]

VIEW_W = 700
CELL_W = 70
CELL_H = 32
LABEL_W = 90
HEADER_H = 26
GRID_X = LABEL_W + 6
GRID_Y = HEADER_H + 10
NUM_ROWS = 2
NUM_COLS = 8

HEX_BAR_Y = GRID_Y + NUM_ROWS * CELL_H + 20
HEX_BAR_H = 44
VIEW_H = HEX_BAR_Y + HEX_BAR_H + 8

lines = svg_header(VIEW_W, VIEW_H)

# Шапка
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

# Сетка
for row in range(NUM_ROWS):
  ry = GRID_Y + row * CELL_H
  lines.append(t(LABEL_W - 6, ry + 20, BYTE_NAMES[row], size=10, fill=INK,
                 weight="bold", anchor="end"))

  for col in range(NUM_COLS):
    bit_pos = 8 - col
    cx = GRID_X + col * CELL_W

    is_functional = (row, bit_pos) in FUNCTIONAL_BITS
    bit_value = (EXAMPLE_HEX[row] >> (bit_pos - 1)) & 1
    is_set_in_example = is_functional and bit_value == 1

    if is_set_in_example:
      fill, opacity, text_weight = WARN, 0.40, "bold"
    elif is_functional:
      fill, opacity, text_weight = ACCENT_A, 0.18, "normal"
    else:
      fill, opacity, text_weight = SOFT, 1.0, "normal"

    lines.append(
      f'<rect x="{cx}" y="{ry}" width="{CELL_W - 1}" height="{CELL_H - 1}" '
      f'fill="{fill}" fill-opacity="{opacity}" '
      f'stroke="{MUTED}" stroke-width="0.5"/>'
    )

    if is_functional:
      label = LABELS[(row, bit_pos)]
      font_size = 10 if len(label) <= 8 else 9
      lines.append(t(cx + CELL_W / 2, ry + 20, label,
                     size=font_size, fill=INK, weight=text_weight))
    elif row == 1:
      # Байт 2: все RFU
      lines.append(t(cx + CELL_W / 2, ry + 20, "RFU", size=9, fill=MUTED))

# Hex bar с бинарной развёрткой
lines.append(t(LABEL_W - 6, HEX_BAR_Y + 18, "Пример:", size=10, fill=MUTED,
               weight="bold", anchor="end"))

for col in range(2):
  cx = GRID_X + col * (CELL_W * 8 / 2)
  box_w = CELL_W * 8 / 2 - 6
  byte = EXAMPLE_HEX[col]

  has_set = any(
    (col, b) in FUNCTIONAL_BITS and (byte >> (b - 1)) & 1 for b in range(1, 9)
  )
  fill = WARN if has_set else SOFT
  opacity = 0.40 if has_set else 1.0
  text_weight = "bold" if has_set else "normal"

  lines.append(
    f'<rect x="{cx}" y="{HEX_BAR_Y}" width="{box_w}" height="{HEX_BAR_H}" '
    f'fill="{fill}" fill-opacity="{opacity}" '
    f'stroke="{MUTED}" stroke-width="0.5"/>'
  )
  lines.append(t(cx + box_w / 2, HEX_BAR_Y + 18, f"0x{byte:02X}",
                 size=12, fill=INK, weight=text_weight))
  bin_str = f"{byte:08b}"
  bin_formatted = f"{bin_str[:4]} {bin_str[4:]}"
  lines.append(t(cx + box_w / 2, HEX_BAR_Y + 35, bin_formatted,
                 size=10, fill=MUTED))

lines.append("</svg>")

write_svg(figures_dir() / "ch07-emv" / "tsi-anatomy.svg", lines)
