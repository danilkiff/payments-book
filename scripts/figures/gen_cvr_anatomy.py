"""Генератор cvr-anatomy.svg для гл. 7 EMV (CVR, карта глазами карты).

CVR (Card Verification Results) -- результаты проверок на~стороне карты,
зеркало TVR. Раскладка по~CCD Format A (EMV Book 3, Part V, Table CCD 10):
4 значащих байта внутри IAD (тег 9F10); пятый байт RFU и~не~показан.
Нибл-поля (тип AC, счётчик попыток PIN, число команд скрипта) шире 1~бита --
подписан левый бит поля, остальные ячейки поля затенены как определённые.
Жёлтым подсвечен пример CVR = 0x28 38 00 00: 1-й GENERATE AC вернул ARQC,
выполнена CDA, офлайн-PIN проверён, остаток попыток PIN = 3.
Источник: emvco-book3 + проза § CVR.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, SOFT, ACCENT_A, WARN,
  figures_dir, t, write_svg, svg_header,
)

# (byte_idx 0..3, bit_pos 1..8) -> подпись. Левый бит нибл-поля несёт имя,
# остальные ячейки поля только затеняются (см. DEFINED).
LABELS = {
  (0, 8): "AC 2-й", (0, 6): "AC 1-й",
  (0, 4): "CDA", (0, 3): "DDA офл", (0, 2): "IA нет", (0, 1): "IA пров",
  (1, 8): "PTC",
  (1, 4): "офл PIN", (1, 3): "PIN✗", (1, 2): "PTL", (1, 1): "онл✗",
  (2, 8): "ниж N", (2, 7): "вер N", (2, 6): "ниж S", (2, 5): "вер S",
  (3, 8): "N скр",
  (3, 4): "скр✗", (3, 3): "ODA пр", (3, 2): "онл сл", (3, 1): "!онл",
}

# Определённые (затеняемые) ячейки: включая нибл-поля без отдельной подписи.
DEFINED = {
  (0, 8), (0, 7), (0, 6), (0, 5), (0, 4), (0, 3), (0, 2), (0, 1),
  (1, 8), (1, 7), (1, 6), (1, 5), (1, 4), (1, 3), (1, 2), (1, 1),
  (2, 8), (2, 7), (2, 6), (2, 5),
  (3, 8), (3, 7), (3, 6), (3, 5), (3, 4), (3, 3), (3, 2), (3, 1),
}

BYTE_NAMES = ["1: AC + аутент.", "2: PIN", "3: лимиты", "4: скрипт"]

# Пример: CVR = 0x28 38 00 00 (4 значащих байта; 5-й RFU)
EXAMPLE_HEX = [0x28, 0x38, 0x00, 0x00]

VIEW_W = 700
CELL_W = 70
CELL_H = 30
LABEL_W = 108
HEADER_H = 26
GRID_X = LABEL_W + 6
GRID_Y = HEADER_H + 10
NUM_ROWS = 4
NUM_COLS = 8

HEX_BAR_Y = GRID_Y + NUM_ROWS * CELL_H + 18
HEX_BAR_H = 42
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

    is_defined = (row, bit_pos) in DEFINED
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

    label = LABELS.get((row, bit_pos))
    if label:
      font_size = 10 if len(label) <= 7 else 9
      lines.append(t(cx + CELL_W / 2, ry + 19, label,
                     size=font_size, fill=INK, weight=text_weight))

# Hex bar с~бинарной развёрткой под каждым байтом
lines.append(t(LABEL_W - 6, HEX_BAR_Y + 16, "Пример:", size=10, fill=MUTED,
               weight="bold", anchor="end"))

for col in range(NUM_ROWS):
  cx = GRID_X + col * (CELL_W * NUM_COLS / NUM_ROWS)
  box_w = CELL_W * NUM_COLS / NUM_ROWS - 4
  byte = EXAMPLE_HEX[col]

  has_set = any((col, b) in DEFINED and (byte >> (b - 1)) & 1
                for b in range(1, 9))
  fill = WARN if has_set else SOFT
  opacity = 0.18 if has_set else 1.0
  text_weight = "bold" if has_set else "normal"

  lines.append(
    f'<rect x="{cx}" y="{HEX_BAR_Y}" width="{box_w}" height="{HEX_BAR_H}" '
    f'fill="{fill}" fill-opacity="{opacity}" '
    f'stroke="{MUTED}" stroke-width="0.5"/>'
  )
  lines.append(t(cx + box_w / 2, HEX_BAR_Y + 17, f"0x{byte:02X}",
                 size=11, fill=INK, weight=text_weight))
  bin_str = f"{byte:08b}"
  bin_formatted = f"{bin_str[:4]} {bin_str[4:]}"
  lines.append(t(cx + box_w / 2, HEX_BAR_Y + 33, bin_formatted,
                 size=9, fill=MUTED))

lines.append("</svg>")

write_svg(figures_dir() / "ch07-emv" / "cvr-anatomy.svg", lines)
