"""Генератор cvm-list-anatomy.svg для гл. 7 EMV (CVM List, тег 8E).

CVM List = две суммы X и~Y (по~4 байта) + список Cardholder Verification
Rules по~2 байта: байт CVM Code (бит~7 -- «применить следующее правило при
неуспехе», биты 6--1 -- код метода) и~байт Condition Code.
Пример: 8E 0E | X=00000000 | Y=00000000 | 4403 | 4203 | 1F00 --
офлайн enciphered PIN, иначе online PIN, иначе No CVM.
Источник: emvco-book3, §10.5.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, SOFT, PANEL, ACCENT_A, ACCENT_B, WARN,
  figures_dir, t, write_svg, svg_header,
)

# Поля стрипа: (подпись_hex, ширина_в_ячейках, имя, цвет)
FIELDS = [
  ("8E", 1, "тег", MUTED),
  ("0E", 1, "L", MUTED),
  ("00 00 00 00", 4, "X (сумма)", ACCENT_A),
  ("00 00 00 00", 4, "Y (сумма)", ACCENT_B),
  ("44 03", 2, "правило 1", ACCENT_A),
  ("42 03", 2, "правило 2", ACCENT_B),
  ("1F 00", 2, "правило 3", ACCENT_A),
]

# Таблица разбора правил: (hex, байт1, байт2, смысл)
RULES = [
  ("44 03", "след. + код 04", "усл. 03", "Offline enc. PIN, если терминал поддерживает"),
  ("42 03", "след. + код 02", "усл. 03", "Online PIN, если терминал поддерживает"),
  ("1F 00", "стоп + код 1F", "усл. 00", "No CVM, всегда (fallback)"),
]

VIEW_W = 600
CELL_W = 26
CELL_H = 26
STRIP_X = 8
STRIP_Y = 16
GAP = 6
LBL_BELOW = 28

TBL_Y = STRIP_Y + CELL_H + LBL_BELOW + 14
TBL_ROW_H = 24
COL_HEX = 64
COL_B1 = 120
COL_B2 = 70
TBL_X_HEX = 8
TBL_X_B1 = TBL_X_HEX + COL_HEX
TBL_X_B2 = TBL_X_B1 + COL_B1
TBL_X_SENSE = TBL_X_B2 + COL_B2

VIEW_H = TBL_Y + (1 + len(RULES)) * TBL_ROW_H + 8

lines = svg_header(VIEW_W, VIEW_H)

# Стрип
x = STRIP_X
for hexstr, ncell, name, color in FIELDS:
  w = ncell * CELL_W
  lines.append(
    f'<rect x="{x}" y="{STRIP_Y}" width="{w}" height="{CELL_H}" '
    f'fill="{color}" fill-opacity="0.15" stroke="{MUTED}" stroke-width="0.5"/>'
  )
  lines.append(t(x + w / 2, STRIP_Y + 17, hexstr, size=10, fill=INK, weight="bold"))
  lines.append(t(x + w / 2, STRIP_Y + CELL_H + 14, name, size=9, fill=MUTED))
  x += w + GAP

# Таблица разбора правил
hdr_y = TBL_Y
lines.append(f'<rect x="0" y="{hdr_y}" width="{VIEW_W}" height="{TBL_ROW_H}" fill="{PANEL}"/>')
lines.append(t(TBL_X_HEX, hdr_y + 16, "Правило", size=10, fill=MUTED, weight="bold", anchor="start"))
lines.append(t(TBL_X_B1, hdr_y + 16, "Байт 1 (CVM Code)", size=10, fill=MUTED, weight="bold", anchor="start"))
lines.append(t(TBL_X_B2, hdr_y + 16, "Байт 2", size=10, fill=MUTED, weight="bold", anchor="start"))
lines.append(t(TBL_X_SENSE, hdr_y + 16, "Смысл", size=10, fill=MUTED, weight="bold", anchor="start"))

for idx, (hexstr, b1, b2, sense) in enumerate(RULES):
  ry = TBL_Y + (1 + idx) * TBL_ROW_H
  if idx % 2 == 1:
    lines.append(f'<rect x="0" y="{ry}" width="{VIEW_W}" height="{TBL_ROW_H}" fill="{SOFT}"/>')
  lines.append(t(TBL_X_HEX, ry + 16, hexstr, size=11, fill=INK, anchor="start", weight="bold"))
  lines.append(t(TBL_X_B1, ry + 16, b1, size=10, fill=INK, anchor="start"))
  lines.append(t(TBL_X_B2, ry + 16, b2, size=10, fill=INK, anchor="start"))
  lines.append(t(TBL_X_SENSE, ry + 16, sense, size=9, fill=INK, anchor="start"))

lines.append("</svg>")

write_svg(figures_dir() / "ch07-emv" / "cvm-list-anatomy.svg", lines)
