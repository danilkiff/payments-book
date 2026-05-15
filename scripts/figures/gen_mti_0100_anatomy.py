"""Генератор mti-0100-anatomy.svg для гл. 5 ISO 8583.

Полный разбор MTI 0100 в~стиле дамп-анализатора:
- сверху hex-view 10 рядов по 16 байт, ячейки подсвечены по полям;
- снизу таблица: имя поля, тип, смещение, длина, hex, декодированное значение.

Схема каждого поля -- из прозы § 5.5 ("Разбираем MTI 0100 и MTI 0110 до конца").
Парсинг и сверка значений -- samples/ch06-iso8583-anatomy/anatomy.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, PANEL, SOFT, ACCENT_A, ACCENT_B,
  FONT, figures_dir, t, write_svg, svg_header,
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


def fill_for(field, is_ll=False):
  k = field["palette"]
  if k == "mti":
    return PANEL, 1.0
  if k == "bitmap":
    return MUTED, 0.18
  if k == "fixed":
    return ACCENT_A, (0.15 if field["alt"] == 0 else 0.28)
  if k == "llvar":
    op = (0.15 if field["alt"] == 0 else 0.28)
    if is_ll:
      op = 0.45
    return ACCENT_B, op
  return PANEL, 1.0


def swatch(field):
  k = field["palette"]
  if k == "mti":
    return PANEL, 1.0
  if k == "bitmap":
    return MUTED, 0.18
  if k == "fixed":
    return ACCENT_A, 0.20
  if k == "llvar":
    return ACCENT_B, 0.25
  return PANEL, 1.0


TYPE_LABEL = {"mti": "MTI", "bitmap": "Bitmap", "fixed": "fixed", "llvar": "LLVAR"}

byte_to_field = [None] * len(data)
for f in fields:
  for o in range(f["offset"], f["offset"] + f["length"]):
    byte_to_field[o] = f

# Hex view: 12 байт/ряд -> 13 рядов
BPR = 12
CELL_W = 24
CELL_H = 20
ROW_GAP = 3
HV_OFFSET_W = 36
HV_GROUP_GAP = 4
HV_ASCII_PAD = 12
ROWS = (len(data) + BPR - 1) // BPR

HV_X_OFFSET = 8
HV_X_BYTES = HV_X_OFFSET + HV_OFFSET_W
HV_Y_TOP = 24
HV_Y_BYTES = HV_Y_TOP + 6
N_GROUPS = (BPR - 1) // 4
HV_X_ASCII = HV_X_BYTES + BPR * CELL_W + N_GROUPS * HV_GROUP_GAP + HV_ASCII_PAD
HV_W = HV_X_ASCII + BPR * 9 + 6
HV_H = HV_Y_BYTES + ROWS * (CELL_H + ROW_GAP) + 4

# Таблица
TBL_Y = HV_H + 22
TBL_ROW_H = 22
COL_SWATCH = 14
COL_NAME = 145
COL_TYPE = 50
COL_OFF = 48
COL_LEN = 42
COL_VAL = HV_W - (COL_SWATCH + COL_NAME + COL_TYPE + COL_OFF + COL_LEN) - 8
TBL_X_NAME = COL_SWATCH + 6
TBL_X_TYPE = TBL_X_NAME + COL_NAME - 6
TBL_X_OFF = TBL_X_TYPE + COL_TYPE
TBL_X_LEN = TBL_X_OFF + COL_OFF
TBL_X_VAL = TBL_X_LEN + COL_LEN

VIEW_W = HV_W
VIEW_H = TBL_Y + (1 + len(fields)) * TBL_ROW_H + 6

lines = svg_header(VIEW_W, VIEW_H)

# Hex-view header
lines.append(t(HV_X_OFFSET, 16, "Offset", size=10, fill=MUTED, weight="bold", anchor="start"))
hv_bytes_center = HV_X_BYTES + (BPR * CELL_W + N_GROUPS * HV_GROUP_GAP) / 2
lines.append(t(hv_bytes_center, 16, "Hex bytes", size=10, fill=MUTED, weight="bold"))
lines.append(t(HV_X_ASCII, 16, "ASCII", size=10, fill=MUTED, weight="bold", anchor="start"))

# Hex-view rows
for row in range(ROWS):
  y = HV_Y_BYTES + row * (CELL_H + ROW_GAP)
  offset = row * BPR
  lines.append(t(HV_X_OFFSET + HV_OFFSET_W - 4, y + 13, f"{offset:04X}",
                 size=10, fill=MUTED, anchor="end"))
  ascii_chars = []
  for col in range(BPR):
    i = offset + col
    if i >= len(data):
      break
    extra = (col // 4) * HV_GROUP_GAP
    cx = HV_X_BYTES + col * CELL_W + extra
    f = byte_to_field[i]
    is_ll = (f["ll_len"] > 0 and i - f["offset"] < f["ll_len"])
    fill, op = fill_for(f, is_ll=is_ll)
    lines.append(
      f'<rect x="{cx}" y="{y}" width="{CELL_W}" height="{CELL_H}" '
      f'fill="{fill}" fill-opacity="{op}"/>'
    )
    lines.append(t(cx + CELL_W / 2, y + 14, f"{data[i]:02X}",
                   size=11, fill=INK))
    b = data[i]
    ascii_chars.append(chr(b) if 32 <= b < 127 else ".")
  lines.append(t(HV_X_ASCII, y + 14, "".join(ascii_chars),
                 size=11, fill=INK, anchor="start"))

# Table header
hdr_y = TBL_Y
lines.append(f'<rect x="0" y="{hdr_y}" width="{VIEW_W}" height="{TBL_ROW_H}" fill="{SOFT}"/>')
lines.append(t(TBL_X_NAME, hdr_y + 15, "Поле", size=11, fill=MUTED, weight="bold", anchor="start"))
lines.append(t(TBL_X_TYPE, hdr_y + 15, "Тип", size=11, fill=MUTED, weight="bold", anchor="start"))
lines.append(t(TBL_X_OFF, hdr_y + 15, "Off", size=11, fill=MUTED, weight="bold", anchor="start"))
lines.append(t(TBL_X_LEN, hdr_y + 15, "Len", size=11, fill=MUTED, weight="bold", anchor="start"))
lines.append(t(TBL_X_VAL, hdr_y + 15, "Значение", size=11, fill=MUTED, weight="bold", anchor="start"))

# Table rows
for idx, f in enumerate(fields):
  ry = TBL_Y + (1 + idx) * TBL_ROW_H
  if idx % 2 == 1:
    lines.append(f'<rect x="0" y="{ry}" width="{VIEW_W}" height="{TBL_ROW_H}" fill="{SOFT}"/>')
  fill, op = swatch(f)
  lines.append(
    f'<rect x="0" y="{ry + 4}" width="{COL_SWATCH}" height="{TBL_ROW_H - 8}" '
    f'fill="{fill}" fill-opacity="{op}"/>'
  )
  lines.append(t(TBL_X_NAME, ry + 15, f["name"], size=11, fill=INK, anchor="start"))
  lines.append(t(TBL_X_TYPE, ry + 15, TYPE_LABEL[f["palette"]], size=10, fill=MUTED, anchor="start"))
  lines.append(t(TBL_X_OFF, ry + 15, f'{f["offset"]:#04x}', size=10, fill=MUTED, anchor="start"))
  lines.append(t(TBL_X_LEN, ry + 15, f'{f["length"]} B', size=10, fill=MUTED, anchor="start"))

  raw = f["raw"]
  if f["name"] == "Bitmap":
    des = []
    for bi, byte in enumerate(raw):
      for bit in range(8):
        if byte & (1 << (7 - bit)):
          de = bi * 8 + bit + 1
          if de != 1:
            des.append(de)
    val = "DE " + ", ".join(str(d) for d in des)
  else:
    if f["ll_len"] > 0:
      ll = raw[:f["ll_len"]].decode("ascii")
      v = raw[f["ll_len"]:].decode("ascii", errors="replace")
      val = f'LL={ll}, "{v}"'
    else:
      val = '"' + raw.decode("ascii", errors="replace") + '"'
  max_chars = 38 if f["name"] != "Bitmap" else 44
  if len(val) > max_chars:
    val = val[:max_chars - 1] + "…"
  lines.append(t(TBL_X_VAL, ry + 15, val, size=11, fill=INK, anchor="start"))

lines.append("</svg>")

write_svg(figures_dir() / "ch06-iso8583" / "mti-0100-anatomy.svg", lines)
