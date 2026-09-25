"""Генератор luhn-check.svg для гл. 4, алгоритм Луна (luhn-patent).

PAN 4561 2612 3456 0892 разложен поразрядно двумя рядами по~восемь цифр:
позиция справа, цифра, удвоение каждой второй цифры справа, результат.
Сумма результатов 67 не кратна 10: номер проверку не~проходит.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  ACCENT_A, BAD, CANVAS_W, FONT, FS_BODY, FS_NOTE, INK, MUTED, PANEL, RX,
  SOFT, SW_BOX, TIER_LIGHT, figures_dir, svg_header_pt, text_width,
  write_svg, xml_escape,
)

PAN = "4561261234560892"

LABEL_W = 58
CELL_W = 39
CELL_H = 16
GROUP_GAP = 6
ROW_GAP = 2
POS_H = 10
BLOCK_GAP = 10
SUM_H = 20


def txt(x, y, s, size=FS_BODY, weight="normal", fill=INK, anchor="middle"):
  attrs = f' font-size="{size}"'
  if weight != "normal":
    attrs += f' font-weight="{weight}"'
  if fill != INK:
    attrs += f' fill="{fill}"'
  if anchor != "start":
    attrs += f' text-anchor="{anchor}"'
  return f'<text x="{x:g}" y="{y:g}"{attrs}>{xml_escape(s)}</text>'


def cell(x, y, fill, op=None, stroke=None):
  o = f' fill-opacity="{op}"' if op is not None else ""
  s = f' stroke="{stroke}" stroke-width="{SW_BOX}"' if stroke else ""
  return (
    f'<rect x="{x:g}" y="{y:g}" width="{CELL_W - 1}" height="{CELL_H}" '
    f'rx="{RX}" fill="{fill}"{o}{s}/>'
  )


digits = [int(c) for c in PAN]
n = len(digits)
rows = []
for i, d in enumerate(digits):
  pos = n - i
  doubled = pos % 2 == 0
  if doubled:
    v = 2 * d
    res = v - 9 if v > 9 else v
    note = f"{v}-9={res}" if v > 9 else str(v)
  else:
    res, note = d, ""
  rows.append((pos, d, doubled, note, res))
total = sum(r[4] for r in rows)
assert total == 67

x0 = LABEL_W + 2
out = []
y = 2
for block in (rows[:8], rows[8:]):
  labels = [
    ("Позиция", y + POS_H - 2),
    ("Цифра", y + POS_H + CELL_H - 4),
    ("Удвоение", y + POS_H + CELL_H + ROW_GAP + CELL_H - 4),
    ("Результат", y + POS_H + 2 * (CELL_H + ROW_GAP) + CELL_H - 4),
  ]
  out.append("<g>")
  for s, ly in labels:
    out.append(txt(LABEL_W - 4, ly, s, weight="bold", fill=MUTED, anchor="end"))
  out.append("</g>")
  for j, (pos, d, doubled, note, res) in enumerate(block):
    x = x0 + j * CELL_W + (GROUP_GAP if j >= 4 else 0)
    cx = x + (CELL_W - 1) / 2
    yd = y + POS_H
    yu = yd + CELL_H + ROW_GAP
    yr = yu + CELL_H + ROW_GAP
    out.append("<g>")
    out.append(txt(cx, y + POS_H - 2, str(pos), size=FS_NOTE, fill=MUTED))
    out.append(cell(x, yd, PANEL))
    out.append(txt(cx, yd + CELL_H - 4, str(d), weight="bold"))
    if doubled:
      out.append(cell(x, yu, ACCENT_A, TIER_LIGHT[0], ACCENT_A))
      out.append(txt(cx, yu + CELL_H - 4, note, weight="bold"))
      out.append(cell(x, yr, ACCENT_A, TIER_LIGHT[0]))
      out.append(txt(cx, yr + CELL_H - 4, str(res), weight="bold"))
    else:
      out.append(cell(x, yu, SOFT))
      out.append(cell(x, yr, PANEL))
      out.append(txt(cx, yr + CELL_H - 4, str(res)))
    out.append("</g>")
  y += POS_H + 3 * CELL_H + 2 * ROW_GAP + BLOCK_GAP

sum_w = 8 * CELL_W + GROUP_GAP - 1
expr = "+".join(str(r[4]) for r in rows) + f" = {total}, не кратна 10"
assert text_width(expr, FS_BODY, "bold") < sum_w - 8
out.append("<g>")
out.append(txt(LABEL_W - 4, y + SUM_H / 2 + 3, "Сумма", weight="bold",
               fill=MUTED, anchor="end"))
out.append(
  f'<rect x="{x0}" y="{y}" width="{sum_w}" height="{SUM_H}" rx="{RX}" '
  f'fill="{BAD}" fill-opacity="0.15" stroke="{BAD}" stroke-width="{SW_BOX}"/>'
)
out.append(txt(x0 + sum_w / 2, y + SUM_H / 2 + 3, expr, weight="bold"))
out.append("</g>")
height = y + SUM_H + 2
width = x0 + sum_w + 2
assert width <= CANVAS_W

lines = svg_header_pt(width, height)
lines.append(f'<g font-family="{FONT}" fill="{INK}">')
lines += out
lines.append("</g>")
lines.append("</svg>")

if __name__ == "__main__":
  write_svg(figures_dir() / "ch04-card-data" / "luhn-check.svg", lines)
