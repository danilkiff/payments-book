"""Генератор pdol-anatomy.svg для гл. 7 EMV.

PDOL = Processing Options Data Object List, тег 0x9F38. Усечённая
TLV-структура: пары (тег, длина) без значений.
Конкретный пример из § 7: бесконтактная Visa объявляет PDOL
9F66 04 | 9F02 06 | 9F37 04 | 5F2A 02 | 9F1A 02.
Источник: emvco-book3, visa-tadg.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, SOFT, ACCENT_A, ACCENT_B,
  figures_dir, t, write_svg, svg_header,
)

# 5 пар (tag_hex, length, ru_name, en_name)
PAIRS = [
  ("9F66", 4, "TTQ", "Terminal Transaction Qualifiers"),
  ("9F02", 6, "сумма", "Authorized Amount"),
  ("9F37", 4, "непредсказуемое число", "Unpredictable Number"),
  ("5F2A", 2, "код валюты", "Transaction Currency Code"),
  ("9F1A", 2, "код страны", "Terminal Country Code"),
]

VIEW_W = 540
CELL_W = 28
CELL_H = 24
HEX_X = 30
HEX_Y = 24
PAIR_GAP = 8
LBL_BELOW = 30

TBL_Y_OFFSET = 90
TBL_ROW_H = 24
COL_SWATCH = 14
COL_HEX = 100
COL_TAG = 70
COL_LEN = 48
COL_NAME = VIEW_W - COL_SWATCH - COL_HEX - COL_TAG - COL_LEN - 8 - 8

TBL_X_HEX = COL_SWATCH + 6
TBL_X_TAG = TBL_X_HEX + COL_HEX
TBL_X_LEN = TBL_X_TAG + COL_TAG
TBL_X_NAME = TBL_X_LEN + COL_LEN

VIEW_H = TBL_Y_OFFSET + (1 + len(PAIRS)) * TBL_ROW_H + 8

lines = svg_header(VIEW_W, VIEW_H)

# Hex strip
x = HEX_X
for idx, (tag_hex, length, name_ru, name_en) in enumerate(PAIRS):
  color = ACCENT_A if idx % 2 == 0 else ACCENT_B
  tag_bytes = [tag_hex[:2], tag_hex[2:]]
  length_byte = f"{length:02X}"

  for i, hb in enumerate(tag_bytes):
    cx = x + i * CELL_W
    lines.append(
      f'<rect x="{cx}" y="{HEX_Y}" width="{CELL_W - 1}" height="{CELL_H}" '
      f'fill="{color}" fill-opacity="0.18" '
      f'stroke="{MUTED}" stroke-width="0.5"/>'
    )
    lines.append(t(cx + CELL_W / 2, HEX_Y + 16, hb, size=11, fill=INK, weight="bold"))

  cx = x + 2 * CELL_W
  lines.append(
    f'<rect x="{cx}" y="{HEX_Y}" width="{CELL_W - 1}" height="{CELL_H}" '
    f'fill="{color}" fill-opacity="0.40" '
    f'stroke="{MUTED}" stroke-width="0.5"/>'
  )
  lines.append(t(cx + CELL_W / 2, HEX_Y + 16, length_byte, size=11, fill=INK, weight="bold"))

  tag_center = x + CELL_W
  lines.append(t(tag_center, HEX_Y + LBL_BELOW + 5, "тег", size=9, fill=MUTED))
  lines.append(t(cx + CELL_W / 2, HEX_Y + LBL_BELOW + 5, "L", size=9, fill=MUTED))

  x += 3 * CELL_W + PAIR_GAP

# Таблица
hdr_y = TBL_Y_OFFSET
lines.append(f'<rect x="0" y="{hdr_y}" width="{VIEW_W}" height="{TBL_ROW_H}" fill="{SOFT}"/>')
lines.append(t(TBL_X_HEX, hdr_y + 16, "Hex", size=10, fill=MUTED, weight="bold", anchor="start"))
lines.append(t(TBL_X_TAG, hdr_y + 16, "Тег", size=10, fill=MUTED, weight="bold", anchor="start"))
lines.append(t(TBL_X_LEN, hdr_y + 16, "Len", size=10, fill=MUTED, weight="bold", anchor="start"))
lines.append(t(TBL_X_NAME, hdr_y + 16, "Запрошенное значение", size=10,
               fill=MUTED, weight="bold", anchor="start"))

for idx, (tag_hex, length, name_ru, name_en) in enumerate(PAIRS):
  ry = TBL_Y_OFFSET + (1 + idx) * TBL_ROW_H
  color = ACCENT_A if idx % 2 == 0 else ACCENT_B
  if idx % 2 == 1:
    lines.append(f'<rect x="0" y="{ry}" width="{VIEW_W}" height="{TBL_ROW_H}" fill="{SOFT}"/>')
  lines.append(
    f'<rect x="0" y="{ry + 4}" width="{COL_SWATCH}" height="{TBL_ROW_H - 8}" '
    f'fill="{color}" fill-opacity="0.22"/>'
  )
  hex_str = f"{tag_hex[:2]} {tag_hex[2:]} {length:02X}"
  lines.append(t(TBL_X_HEX, ry + 16, hex_str, size=11, fill=INK, anchor="start", weight="bold"))
  lines.append(t(TBL_X_TAG, ry + 16, f"0x{tag_hex}", size=11, fill=INK, anchor="start"))
  lines.append(t(TBL_X_LEN, ry + 16, f"{length} B", size=10, fill=MUTED, anchor="start"))
  lines.append(t(TBL_X_NAME, ry + 16, f"{name_ru} ({name_en})",
                 size=10, fill=INK, anchor="start"))

lines.append("</svg>")

write_svg(figures_dir() / "ch07-emv" / "pdol-anatomy.svg", lines)
