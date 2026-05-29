"""Генератор csu-anatomy.svg для гл. 7 EMV (CSU, ответ эмитента карте).

CSU (Card Status Update) -- 4 байта внутри Issuer Authentication Data (тег 91)
рядом с ARPC. Инструктирует чип после онлайн-ответа: одобрение, блокировка
карты/приложения, обновление счётчика попыток PIN, признак «онлайн в след. раз»,
обновление офлайн-счётчиков (2 бита). Байт 1 -- нибл PTC; байт 3 RFU; байт 4 --
ID профилей сброса счётчиков.
Пример: CSU = 0x00 82 00 00 -- эмитент одобряет и сбрасывает офлайн-счётчики.
Источник: emvco-book3, Table CCD 11.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, SOFT, ACCENT_A, WARN,
  figures_dir, t, write_svg, svg_header,
)

LABELS = {
  (0, 8): "пропр.", (0, 4): "PTC",
  (1, 8): "одобр.", (1, 7): "карта✗", (1, 6): "прил.✗", (1, 5): "обн.PTC",
  (1, 4): "онл.след", (1, 3): "proxy", (1, 2): "счётч.",
  (3, 8): "профиль 1", (3, 4): "профиль 2",
}
DEFINED = {
  (0, 8), (0, 4), (0, 3), (0, 2), (0, 1),
  (1, 8), (1, 7), (1, 6), (1, 5), (1, 4), (1, 3), (1, 2), (1, 1),
  (3, 8), (3, 7), (3, 6), (3, 5), (3, 4), (3, 3), (3, 2), (3, 1),
}
BYTE_NAMES = ["1: PTC", "2: действия", "3: RFU", "4: профили"]
EXAMPLE_HEX = [0x00, 0x82, 0x00, 0x00]

VIEW_W = 700
CELL_W = 70
CELL_H = 30
LABEL_W = 112
HEADER_H = 26
GRID_X = LABEL_W + 6
GRID_Y = HEADER_H + 10
NUM_ROWS = 4
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
      font_size = 10 if len(label) <= 7 else 9
      lines.append(t(cx + CELL_W / 2, ry + 19, label, size=font_size, fill=INK, weight=weight))

lines.append(t(LABEL_W - 6, HEX_BAR_Y + 16, "Пример:", size=10, fill=MUTED,
               weight="bold", anchor="end"))
for col in range(NUM_ROWS):
  cx = GRID_X + col * (CELL_W * NUM_COLS / NUM_ROWS)
  box_w = CELL_W * NUM_COLS / NUM_ROWS - 4
  byte = EXAMPLE_HEX[col]
  has_set = any((col, b) in DEFINED and (byte >> (b - 1)) & 1 for b in range(1, 9))
  fill = WARN if has_set else SOFT
  opacity = 0.18 if has_set else 1.0
  weight = "bold" if has_set else "normal"
  lines.append(
    f'<rect x="{cx}" y="{HEX_BAR_Y}" width="{box_w}" height="{HEX_BAR_H}" '
    f'fill="{fill}" fill-opacity="{opacity}" stroke="{MUTED}" stroke-width="0.5"/>'
  )
  lines.append(t(cx + box_w / 2, HEX_BAR_Y + 17, f"0x{byte:02X}", size=11, fill=INK, weight=weight))
  bin_str = f"{byte:08b}"
  lines.append(t(cx + box_w / 2, HEX_BAR_Y + 33, f"{bin_str[:4]} {bin_str[4:]}", size=9, fill=MUTED))

lines.append("</svg>")
write_svg(figures_dir() / "ch07-emv" / "csu-anatomy.svg", lines)
