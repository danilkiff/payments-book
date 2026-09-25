"""Генератор bitmap-presence.svg для гл. 6 ISO 8583, раздел о~bitmap.

8 рядов (по~байту primary bitmap MTI 0100) x 8 ячеек (биты MSB->LSB).
Заполненные ячейки -- присутствующие DE; пустые -- отсутствующие.
Бит 1 первого байта -- флаг расширения (secondary bitmap), здесь 0.
Источник раскладки -- fis-iso8583-guide-2023.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  ACCENT_A, FONT, FS_BODY, FS_NOTE, INK, MUTED, SOFT, SW_FRAME, TIER_LIGHT,
  figures_dir, svg_header_pt, write_svg, xml_escape,
)

BITMAP_HEX = "72 3C 04 81 20 C0 80 00"
bitmap = bytes.fromhex(BITMAP_HEX.replace(" ", ""))

CELL_W = 40
CELL_H = 22
GRID_X = 36
GRID_Y = 14
MARGIN = 2


def txt(x, y, s, size=FS_BODY, weight="normal", fill=INK, anchor="middle"):
  attrs = f' font-size="{size}"'
  if weight != "normal":
    attrs += f' font-weight="{weight}"'
  if fill != INK:
    attrs += f' fill="{fill}"'
  if anchor != "start":
    attrs += f' text-anchor="{anchor}"'
  return f'<text x="{x:g}" y="{y:g}"{attrs}>{xml_escape(s)}</text>'


out = ["<g>"]
out.append(txt(GRID_X - 5, GRID_Y - 4, "Hex", FS_NOTE, "bold", MUTED, "end"))
for col in range(8):
  cx = GRID_X + col * CELL_W + CELL_W / 2
  out.append(txt(cx, GRID_Y - 4, str(col + 1), FS_NOTE, "bold", MUTED))
out.append("</g>")

for row in range(8):
  byte = bitmap[row]
  y = GRID_Y + row * CELL_H
  out.append("<g>")
  out.append(txt(GRID_X - 5, y + CELL_H / 2 + 3, f"0x{byte:02X}", weight="bold",
                 anchor="end"))
  for col in range(8):
    bit_pos = row * 8 + col + 1
    is_set = bool(byte & (1 << (7 - col)))
    x = GRID_X + col * CELL_W
    if is_set:
      fill = f'fill="{ACCENT_A}" fill-opacity="{TIER_LIGHT[0]}"'
    else:
      fill = f'fill="{SOFT}"'
    out.append(
      f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" {fill} '
      f'stroke="{MUTED}" stroke-width="{SW_FRAME}"/>'
    )
    if is_set:
      label = f"DE {bit_pos}" if bit_pos >= 2 else "+64"
      out.append(txt(x + CELL_W / 2, y + CELL_H / 2 + 3, label, weight="bold"))
  out.append("</g>")

width = GRID_X + 8 * CELL_W + MARGIN
height = GRID_Y + 8 * CELL_H + MARGIN
lines = svg_header_pt(width, height)
lines.append(f'<g font-family="{FONT}" fill="{INK}">')
lines += out
lines += ["</g>", "</svg>"]

if __name__ == "__main__":
  write_svg(figures_dir() / "ch06-iso8583" / "bitmap-presence.svg", lines)
