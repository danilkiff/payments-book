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
  ACCENT_A, CANVAS_W, FONT, FS_BODY, FS_NOTE, MUTED, PANEL, SOFT, SW_FRAME,
  TIER_LIGHT, figures_dir, svg_header_pt, t, write_svg, zebra,
)

# Поля стрипа: (hex, ширина в ячейках, имя, тон). Смежные поля ACCENT_A
# различаются светлотой (zebra TIER_LIGHT), тег и длина -- нейтральный Panel.
FIELDS = [
  ("8E", 1, "тег", None),
  ("0E", 1, "L", None),
  ("00 00 00 00", 4, "X (сумма)", ACCENT_A),
  ("00 00 00 00", 4, "Y (сумма)", ACCENT_A),
  ("44 03", 2, "правило 1", ACCENT_A),
  ("42 03", 2, "правило 2", ACCENT_A),
  ("1F 00", 2, "правило 3", ACCENT_A),
]

# Таблица разбора правил: (hex, байт1, байт2, смысл)
RULES = [
  ("44 03", "след. + код 04", "усл. 03", "Offline enc. PIN, если терминал поддерживает"),
  ("42 03", "след. + код 02", "усл. 03", "Online PIN, если терминал поддерживает"),
  ("1F 00", "стоп + код 1F", "усл. 00", "No CVM, всегда (fallback)"),
]

W = CANVAS_W
CELL_W = 20
CELL_H = 16
GAP = 5
STRIP_Y = 2
STRIP_W = sum(n for _, n, _, _ in FIELDS) * CELL_W + (len(FIELDS) - 1) * GAP
STRIP_X = (W - STRIP_W) / 2

ROW_H = 14
TBL_Y = STRIP_Y + CELL_H + 18
X_HEX = 4
X_B1 = X_HEX + 44
X_B2 = X_B1 + 86
X_SENSE = X_B2 + 44
H = TBL_Y + (1 + len(RULES)) * ROW_H + 2


def build():
  out = []
  x = STRIP_X
  alt = 0
  for hexstr, ncell, name, tone in FIELDS:
    w = ncell * CELL_W
    if tone is None:
      fill = f'fill="{PANEL}"'
    else:
      fill = f'fill="{tone}" fill-opacity="{zebra(TIER_LIGHT, alt)}"'
      alt = 1 - alt
    out.append(
      f'<rect x="{x:.1f}" y="{STRIP_Y}" width="{w}" height="{CELL_H}" {fill} '
      f'stroke="{MUTED}" stroke-width="{SW_FRAME}"/>'
    )
    out.append(t(f"{x + w / 2:.1f}", STRIP_Y + 11, hexstr, size=FS_BODY,
                 weight="bold"))
    out.append(t(f"{x + w / 2:.1f}", STRIP_Y + CELL_H + 9, name, size=FS_NOTE,
                 fill=MUTED))
    x += w + GAP

  out.append(f'<rect x="0" y="{TBL_Y}" width="{W}" height="{ROW_H}" fill="{PANEL}"/>')
  for cx, s in ((X_HEX, "Правило"), (X_B1, "Байт 1 (CVM Code)"),
                (X_B2, "Байт 2"), (X_SENSE, "Смысл")):
    out.append(t(cx, TBL_Y + 10, s, size=FS_BODY, weight="bold", fill=MUTED,
                 anchor="start"))
  for idx, (hexstr, b1, b2, sense) in enumerate(RULES):
    ry = TBL_Y + (1 + idx) * ROW_H
    if idx % 2 == 1:
      out.append(f'<rect x="0" y="{ry}" width="{W}" height="{ROW_H}" fill="{SOFT}"/>')
    out.append(t(X_HEX, ry + 10, hexstr, size=FS_BODY, weight="bold",
                 anchor="start"))
    out.append(t(X_B1, ry + 10, b1, size=FS_BODY, anchor="start"))
    out.append(t(X_B2, ry + 10, b2, size=FS_BODY, anchor="start"))
    out.append(t(X_SENSE, ry + 10, sense, size=FS_BODY, anchor="start"))
  return svg_header_pt(W, H) + [f'<g font-family="{FONT}">'] + out + ["</g>", "</svg>"]


if __name__ == "__main__":
  write_svg(figures_dir() / "ch07-emv" / "cvm-list-anatomy.svg", build())
