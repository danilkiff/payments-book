"""Генератор tvr-anatomy.svg для гл. 7 EMV § 7.10.

TVR (Terminal Verification Results) -- 5 байт битовых флагов
результатов проверок. Жёлтым подсвечен бит установленного примера
TVR = 0x0000080000 (бит 4 байта 3, PIN entry required, PIN not entered).
Источник: emvco-book3 + проза § 7.10.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, SOFT, ACCENT_A, WARN,
  figures_dir, t, write_svg, svg_header,
)

# (byte_idx 0..4, bit_pos 1..8) -> short label
LABELS = {
  (0, 8): "ODA нет",
  (0, 7): "SDA✗",
  (0, 6): "ICC нет",
  (0, 5): "excl.file",
  (0, 4): "DDA✗",
  (0, 3): "CDA✗",
  (1, 8): "ver≠",
  (1, 7): "просроч.",
  (1, 6): "не действ.",
  (1, 5): "услуга✗",
  (1, 4): "новая",
  (2, 8): "CVM✗",
  (2, 7): "CVM ?",
  (2, 6): "PIN исч.",
  (2, 5): "пада нет",
  (2, 4): "PIN нет",
  (2, 3): "PIN онл.",
  (3, 8): "floor",
  (3, 7): "ниж.лим.",
  (3, 6): "верх.лим.",
  (3, 5): "random",
  (3, 4): "force",
  (4, 8): "TDOL deflt",
  (4, 7): "ARPC✗",
  (4, 6): "scr-pre",
  (4, 5): "scr-post",
}

BYTE_NAMES = ["1: данные", "2: терминал", "3: CVM", "4: риск", "5: прочее"]

# Пример: TVR = 0x0000080000
EXAMPLE_HEX = [0x00, 0x00, 0x08, 0x00, 0x00]

VIEW_W = 700
CELL_W = 70
CELL_H = 30
LABEL_W = 100
HEADER_H = 26
GRID_X = LABEL_W + 6
GRID_Y = HEADER_H + 10
NUM_ROWS = 5
NUM_COLS = 8

HEX_BAR_Y = GRID_Y + NUM_ROWS * CELL_H + 18
HEX_BAR_H = 42  # выше обычного, чтобы вместить hex + бинарную развёртку
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
  lines.append(t(LABEL_W - 6, ry + 19, BYTE_NAMES[row], size=10, fill=INK,
                 weight="bold", anchor="end"))

  for col in range(NUM_COLS):
    bit_pos = 8 - col
    cx = GRID_X + col * CELL_W

    is_defined = (row, bit_pos) in LABELS
    bit_value = (EXAMPLE_HEX[row] >> (bit_pos - 1)) & 1
    is_set_in_example = is_defined and bit_value == 1

    if is_set_in_example:
      fill, opacity, text_weight = WARN, 0.18, "bold"
    elif is_defined:
      fill, opacity, text_weight = ACCENT_A, 0.15, "normal"
    else:
      fill, opacity, text_weight = SOFT, 1.0, "normal"

    lines.append(
      f'<rect x="{cx}" y="{ry}" width="{CELL_W - 1}" height="{CELL_H - 1}" '
      f'fill="{fill}" fill-opacity="{opacity}" '
      f'stroke="{MUTED}" stroke-width="0.5"/>'
    )

    if is_defined:
      label = LABELS[(row, bit_pos)]
      font_size = 10 if len(label) <= 7 else 9
      lines.append(t(cx + CELL_W / 2, ry + 19, label,
                     size=font_size, fill=INK, weight=text_weight))

# Hex bar с бинарной развёрткой под каждым байтом
lines.append(t(LABEL_W - 6, HEX_BAR_Y + 16, "Пример:", size=10, fill=MUTED,
               weight="bold", anchor="end"))

for col in range(5):
  cx = GRID_X + col * (CELL_W * 8 / 5)
  box_w = CELL_W * 8 / 5 - 4
  byte = EXAMPLE_HEX[col]

  has_set = any((col, b) in LABELS and (byte >> (b - 1)) & 1 for b in range(1, 9))
  fill = WARN if has_set else SOFT
  opacity = 0.18 if has_set else 1.0
  text_weight = "bold" if has_set else "normal"

  lines.append(
    f'<rect x="{cx}" y="{HEX_BAR_Y}" width="{box_w}" height="{HEX_BAR_H}" '
    f'fill="{fill}" fill-opacity="{opacity}" '
    f'stroke="{MUTED}" stroke-width="0.5"/>'
  )
  # Hex значение
  lines.append(t(cx + box_w / 2, HEX_BAR_Y + 17, f"0x{byte:02X}",
                 size=11, fill=INK, weight=text_weight))
  # Бинарная развёртка (MSB слева, как в~сетке выше)
  bin_str = f"{byte:08b}"
  bin_formatted = f"{bin_str[:4]} {bin_str[4:]}"
  lines.append(t(cx + box_w / 2, HEX_BAR_Y + 33, bin_formatted,
                 size=9, fill=MUTED))

lines.append("</svg>")

write_svg(figures_dir() / "ch07-emv" / "tvr-anatomy.svg", lines)
