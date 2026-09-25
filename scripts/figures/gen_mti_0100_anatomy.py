"""Генератор mti-0100-anatomy.svg для гл. 6 ISO 8583.

Hex-дамп MTI 0100 по~12 байт в~ряду, ячейки подсвечены по~типу поля,
легенда типов снизу. Таблица полей (смещение, длина, значение) вынесена
в~LaTeX: tab:mti-0100-fields в~src/parts/part1/ch06-iso8583.tex; при правке
HEX или SCHEMA таблица сверяется с~выводом parse().

Схема каждого поля -- из прозы § 5.5 ("Разбираем MTI 0100 и MTI 0110 до конца").
Парсинг и сверка значений -- samples/ch06-iso8583-anatomy/anatomy.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  ACCENT_A, ACCENT_B, CANVAS_W, FONT, FS_BODY, FS_NOTE, INK, MUTED, PANEL,
  SW_LINK, TIER_DARK, TIER_LIGHT, TIER_LIGHT_MID, TIER_NEUTRAL, TIER_PANEL,
  figures_dir, svg_header_pt, text_width, write_svg, xml_escape, zebra,
)

HEX = """
30 31 30 30
72 3C 04 81 20 C0 80 00
31 36 32 32 30 30 31 32 31 32 33 34 35 36 30 38 39 32
30 30 30 30 30 30
30 30 30 30 30 30 31 32 35 30 35 30
30 33 31 37 31 37 33 30 34 35
34 38 32 37 33 31
31 37 33 30 34 35
30 33 31 37
32 36 31 32
30 37 31
30 30
30 36 31 32 33 34 35 36
33 34 32 32 30 30 31 32 31 32 33 34 35 36 30 38 39 32
3D 32 36 31 32 32 30 31 31 32 33 34 35 36 37 38 39 30
54 45 52 4D 30 30 30 31
4D 45 52 43 48 41 4E 54 30 30 30 30 30 30 31
36 34 33
"""
data = bytes.fromhex(HEX.replace(" ", "").replace("\n", ""))

SCHEMA = [
  ("MTI", "fixed", 4, "mti"),
  ("Bitmap", "fixed", 8, "bitmap"),
  ("DE 2 (PAN)", "llvar", None, "llvar"),
  ("DE 3 (Proc Code)", "fixed", 6, "fixed"),
  ("DE 4 (Amount)", "fixed", 12, "fixed"),
  ("DE 7 (Trans DT)", "fixed", 10, "fixed"),
  ("DE 11 (STAN)", "fixed", 6, "fixed"),
  ("DE 12 (Local Time)", "fixed", 6, "fixed"),
  ("DE 13 (Local Date)", "fixed", 4, "fixed"),
  ("DE 14 (Expiry)", "fixed", 4, "fixed"),
  ("DE 22 (POS Entry)", "fixed", 3, "fixed"),
  ("DE 25 (POS Cond)", "fixed", 2, "fixed"),
  ("DE 32 (Acq Inst)", "llvar", None, "llvar"),
  ("DE 35 (Track 2)", "llvar", None, "llvar"),
  ("DE 41 (Terminal)", "fixed", 8, "fixed"),
  ("DE 42 (Merchant)", "fixed", 15, "fixed"),
  ("DE 49 (Currency)", "fixed", 3, "fixed"),
]


def parse(data, schema):
  out, offset = [], 0
  for name, kind, size, palette in schema:
    start = offset
    if kind == "fixed":
      raw = data[offset:offset + size]
      offset += size
      ll_len = 0
    else:
      length = int(data[offset:offset + 2].decode("ascii"))
      raw = data[offset:offset + 2 + length]
      offset += 2 + length
      ll_len = 2
    out.append({
      "name": name, "offset": start, "length": len(raw),
      "raw": raw, "ll_len": ll_len, "palette": palette,
    })
  return out, offset


fields, consumed = parse(data, SCHEMA)
assert consumed == len(data), f"parse mismatch: {consumed} vs {len(data)}"

# Чередование тона для смежных полей одного типа
last_kind, alt = None, 0
for f in fields:
  k = f["palette"]
  if k in ("fixed", "llvar"):
    alt = 1 - alt if k == last_kind else 0
    last_kind = k
  f["alt"] = alt if k in ("fixed", "llvar") else 0


# Тип поля кодируется тиром светлоты (см. _common.py): fixed -- светлый тир
# ACCENT_A с zebra по смежным полям, llvar -- тёмный тир ACCENT_B, bitmap --
# нейтральный MUTED, mti -- сплошной PANEL. Так типы различимы и при дальтонизме.
def fill_for(field):
  k = field["palette"]
  if k == "mti":
    return PANEL, TIER_PANEL
  if k == "bitmap":
    return MUTED, TIER_NEUTRAL
  if k == "fixed":
    return ACCENT_A, zebra(TIER_LIGHT, field["alt"])
  if k == "llvar":
    return ACCENT_B, TIER_DARK
  return PANEL, TIER_PANEL


byte_to_field = [None] * len(data)
for f in fields:
  for o in range(f["offset"], f["offset"] + f["length"]):
    byte_to_field[o] = f

BPR = 12
CELL_W = 20
CELL_H = 13
ROW_GAP = 2
GROUP_GAP = 4
MARGIN = 2
OFFSET_W = 26
ASCII_PAD = 10
HEAD_H = 12
LEGEND_GAP = 10
SWATCH = 10
ROWS = (len(data) + BPR - 1) // BPR

X_BYTES = MARGIN + OFFSET_W
N_GROUPS = (BPR - 1) // 4
X_ASCII = X_BYTES + BPR * CELL_W + N_GROUPS * GROUP_GAP + ASCII_PAD
Y_BYTES = MARGIN + HEAD_H


def txt(x, y, s, size=FS_BODY, weight="normal", fill=INK, anchor="start"):
  attrs = f' font-size="{size}"'
  if weight != "normal":
    attrs += f' font-weight="{weight}"'
  if fill != INK:
    attrs += f' fill="{fill}"'
  if anchor != "start":
    attrs += f' text-anchor="{anchor}"'
  return f'<text x="{x:g}" y="{y:g}"{attrs}>{xml_escape(s)}</text>'


def rect(x, y, w, h, fill, op):
  o = f' fill-opacity="{op}"' if op != 1.0 else ""
  return (
    f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
    f'fill="{fill}"{o}/>'
  )


def edge(x, y, w):
  """Кромка над~байтом LL-префикса: нецветовой признак переменной длины."""
  return (
    f'<line x1="{x:g}" y1="{y + 0.5:g}" x2="{x + w:g}" y2="{y + 0.5:g}" '
    f'stroke="{MUTED}" stroke-width="{SW_LINK}"/>'
  )


out = ["<g>"]
out.append(txt(MARGIN, MARGIN + 7, "Offset", FS_NOTE, "bold", MUTED))
bytes_w = BPR * CELL_W + N_GROUPS * GROUP_GAP
out.append(txt(X_BYTES + bytes_w / 2, MARGIN + 7, "Hex bytes", FS_NOTE, "bold",
               MUTED, "middle"))
out.append(txt(X_ASCII, MARGIN + 7, "ASCII", FS_NOTE, "bold", MUTED))
out.append("</g>")

ascii_right = 0
for row in range(ROWS):
  y = Y_BYTES + row * (CELL_H + ROW_GAP)
  base = row * BPR
  out.append("<g>")
  out.append(txt(X_BYTES - 4, y + 9.5, f"{base:04X}", fill=MUTED, anchor="end"))
  chars = []
  for col in range(BPR):
    i = base + col
    if i >= len(data):
      break
    x = X_BYTES + col * CELL_W + (col // 4) * GROUP_GAP
    f = byte_to_field[i]
    out.append(rect(x, y, CELL_W, CELL_H, *fill_for(f)))
    if f["ll_len"] and i - f["offset"] < f["ll_len"]:
      out.append(edge(x, y, CELL_W))
    out.append(txt(x + CELL_W / 2, y + 9.5, f"{data[i]:02X}", anchor="middle"))
    chars.append(chr(data[i]) if 32 <= data[i] < 127 else ".")
  line = "".join(chars)
  ascii_right = max(ascii_right, X_ASCII + text_width(line))
  out.append(txt(X_ASCII, y + 9.5, line))
  out.append("</g>")

y_leg = Y_BYTES + ROWS * (CELL_H + ROW_GAP) + LEGEND_GAP
legend = [
  ("MTI", PANEL, TIER_PANEL, False),
  ("Bitmap", MUTED, TIER_NEUTRAL, False),
  ("fixed", ACCENT_A, TIER_LIGHT_MID, False),
  ("LLVAR", ACCENT_B, TIER_DARK, False),
  ("кромка: префикс LL", ACCENT_B, TIER_DARK, True),
]
x = X_BYTES
for label, fill, op, ll in legend:
  out.append("<g>")
  out.append(rect(x, y_leg, SWATCH, SWATCH, fill, op))
  if ll:
    out.append(edge(x, y_leg, SWATCH))
  out.append(txt(x + SWATCH + 4, y_leg + 8, label, FS_NOTE, fill=MUTED))
  out.append("</g>")
  x += SWATCH + 4 + text_width(label, FS_NOTE) + 14

width = round(max(ascii_right, x) + MARGIN)
height = y_leg + SWATCH + MARGIN
assert width <= CANVAS_W, width
lines = svg_header_pt(width, height)
lines.append(f'<g font-family="{FONT}" fill="{INK}">')
lines += out
lines += ["</g>", "</svg>"]

if __name__ == "__main__":
  write_svg(figures_dir() / "ch06-iso8583" / "mti-0100-anatomy.svg", lines)
