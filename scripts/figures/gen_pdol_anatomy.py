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
  ACCENT_A, CANVAS_W, FONT, FS_BODY, FS_NOTE, INK, MUTED, SOFT, SW_FRAME,
  TIER_LIGHT, figures_dir, svg_header_pt, t, write_svg, zebra,
)

# 5 пар (tag_hex, length, ru_name, en_name)
PAIRS = [
  ("9F66", 4, "TTQ", "Terminal Transaction Qualifiers"),
  ("9F02", 6, "сумма", "Authorized Amount"),
  ("9F37", 4, "непредсказуемое число", "Unpredictable Number"),
  ("5F2A", 2, "код валюты", "Transaction Currency Code"),
  ("9F1A", 2, "код страны", "Terminal Country Code"),
]

W = CANVAS_W
CELL_W = 22
CELL_H = 16
PAIR_GAP = 8
STRIP_W = len(PAIRS) * 3 * CELL_W + (len(PAIRS) - 1) * PAIR_GAP
HEX_X = (W - STRIP_W) / 2
HEX_Y = 2

ROW_H = 14
TBL_Y = HEX_Y + CELL_H + 18
SWATCH = 8
X_HEX = SWATCH + 6
X_TAG = X_HEX + 50
X_LEN = X_TAG + 42
X_NAME = X_LEN + 28
H = TBL_Y + (1 + len(PAIRS)) * ROW_H + 2


def cell(x, y, op):
  # Соседние пары различаются светлотой одного оттенка (zebra TIER_LIGHT).
  return (
    f'<rect x="{x:.1f}" y="{y}" width="{CELL_W}" height="{CELL_H}" '
    f'fill="{ACCENT_A}" fill-opacity="{op}" stroke="{MUTED}" '
    f'stroke-width="{SW_FRAME}"/>'
  )


def build():
  out = []
  x = HEX_X
  for idx, (tag_hex, length, _, _) in enumerate(PAIRS):
    op = zebra(TIER_LIGHT, idx % 2)
    for i, hb in enumerate([tag_hex[:2], tag_hex[2:], f"{length:02X}"]):
      cx = x + i * CELL_W
      out.append(cell(cx, HEX_Y, op))
      out.append(t(f"{cx + CELL_W / 2:.1f}", HEX_Y + 11, hb, size=FS_BODY,
                   weight="bold"))
    out.append(t(f"{x + CELL_W:.1f}", HEX_Y + CELL_H + 9, "тег",
                 size=FS_NOTE, fill=MUTED))
    out.append(t(f"{x + 2.5 * CELL_W:.1f}", HEX_Y + CELL_H + 9, "L",
                 size=FS_NOTE, fill=MUTED))
    x += 3 * CELL_W + PAIR_GAP

  out.append(f'<rect x="0" y="{TBL_Y}" width="{W}" height="{ROW_H}" fill="{SOFT}"/>')
  for cx, s in ((X_HEX, "Hex"), (X_TAG, "Тег"), (X_LEN, "Len"),
                (X_NAME, "Запрошенное значение")):
    out.append(t(cx, TBL_Y + 10, s, size=FS_BODY, weight="bold", fill=MUTED,
                 anchor="start"))
  for idx, (tag_hex, length, ru, en) in enumerate(PAIRS):
    ry = TBL_Y + (1 + idx) * ROW_H
    if idx % 2 == 1:
      out.append(f'<rect x="0" y="{ry}" width="{W}" height="{ROW_H}" fill="{SOFT}"/>')
    out.append(
      f'<rect x="0" y="{ry + 3}" width="{SWATCH}" height="{ROW_H - 6}" '
      f'fill="{ACCENT_A}" fill-opacity="{zebra(TIER_LIGHT, idx % 2)}"/>'
    )
    out.append(t(X_HEX, ry + 10, f"{tag_hex[:2]} {tag_hex[2:]} {length:02X}",
                 size=FS_BODY, weight="bold", anchor="start"))
    out.append(t(X_TAG, ry + 10, f"0x{tag_hex}", size=FS_BODY, anchor="start"))
    out.append(t(X_LEN, ry + 10, f"{length} B", size=FS_BODY, fill=MUTED,
                 anchor="start"))
    out.append(t(X_NAME, ry + 10, f"{ru} ({en})", size=FS_BODY, fill=INK,
                 anchor="start"))
  return svg_header_pt(W, H) + [f'<g font-family="{FONT}">'] + out + ["</g>", "</svg>"]


if __name__ == "__main__":
  write_svg(figures_dir() / "ch07-emv" / "pdol-anatomy.svg", build())
