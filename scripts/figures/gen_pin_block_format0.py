"""Генератор pin-block-format0.svg для гл. 10 § 10.5.

ISO 9564 Format 0 -- 8-байтовый PIN-блок, XOR двух 16-ниббловых полей:
- PIN-поле: [0][len][PIN digits][F-padding]
- PAN-поле: [0000][rightmost 12 of PAN без check digit]

Пример: PIN=1234, тестовый PAN Stripe 4242 4242 4242 4242.
Источники: iso-9564, stripe-testing.

Примечание: Inkscape ломает PDF export при наличии символа ⊕ в~SVG.
Здесь используется текст "XOR".
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, SOFT, PANEL, ACCENT_A, ACCENT_B, WARN,
  figures_dir, t, write_svg, svg_header,
)

PIN = "1234"
PAN_FULL = "4242424242424242"

pan_no_check = PAN_FULL[:-1]
pan_rightmost_12 = pan_no_check[-12:]


def build_pin_field(pin_str):
  length = len(pin_str)
  nibbles = ["0", f"{length:X}"] + list(pin_str)
  while len(nibbles) < 16:
    nibbles.append("F")
  return nibbles


def build_pan_field(pan_right_12):
  return ["0", "0", "0", "0"] + list(pan_right_12)


def xor_nibbles(a, b):
  return [f"{int(x, 16) ^ int(y, 16):X}" for x, y in zip(a, b)]


pin_field = build_pin_field(PIN)
pan_field = build_pan_field(pan_rightmost_12)
result = xor_nibbles(pin_field, pan_field)

assert "".join(pin_field) == "041234FFFFFFFFFF"
assert "".join(pan_field) == "0000242424242424"
assert "".join(result) == "041210DBDBDBDBDB"

VIEW_W = 700
LEFT_PAD = 70
CELL_W = 36
CELL_H = 28
ROW_GAP = 50
LABEL_X = LEFT_PAD - 8
ROW_Y_START = 56

PIN_GROUPS = [
  (0, 0, "формат"),
  (1, 1, "длина"),
  (2, 5, "PIN"),
  (6, 15, "F-padding"),
]
PAN_GROUPS = [
  (0, 3, "нули"),
  (4, 15, "правые 12 цифр PAN без check"),
]

PIN_GROUP_COLORS = {
  "формат": (PANEL, 1.0),
  "длина": (PANEL, 1.0),
  "PIN": (ACCENT_A, 0.30),
  "F-padding": (SOFT, 1.0),
}
PAN_GROUP_COLORS = {
  "нули": (SOFT, 1.0),
  "правые 12 цифр PAN без check": (ACCENT_B, 0.30),
}


def group_color_for(nibble_idx, groups, color_map):
  for start, end, label in groups:
    if start <= nibble_idx <= end:
      return color_map[label], label
  return (SOFT, 1.0), ""


lines = svg_header(VIEW_W, 290)

# Input строка
inputs_y = 22
lines.append(t(LEFT_PAD, inputs_y, "Вход:", size=10, fill=MUTED, weight="bold", anchor="start"))
lines.append(t(LEFT_PAD + 50, inputs_y,
               f"PIN = {PIN}; PAN = {PAN_FULL} (check digit = {PAN_FULL[-1]})",
               size=10, fill=INK, anchor="start"))


def draw_row(y, nibbles, groups, color_map, row_label):
  lines.append(t(LABEL_X, y + 18, row_label, size=10, fill=MUTED,
                 weight="bold", anchor="end"))

  for start, end, lbl in groups:
    center_x = LEFT_PAD + (start + (end - start) / 2 + 0.5) * CELL_W
    lines.append(t(center_x, y - 4, lbl, size=8, fill=MUTED))

  for i, nib in enumerate(nibbles):
    cx = LEFT_PAD + i * CELL_W
    (fill, opacity), _ = group_color_for(i, groups, color_map)
    lines.append(
      f'<rect x="{cx}" y="{y}" width="{CELL_W - 1}" height="{CELL_H}" '
      f'fill="{fill}" fill-opacity="{opacity}" '
      f'stroke="{MUTED}" stroke-width="0.5"/>'
    )
    lines.append(t(cx + CELL_W / 2, y + 19, nib, size=12, fill=INK, weight="bold"))


y1 = ROW_Y_START
draw_row(y1, pin_field, PIN_GROUPS, PIN_GROUP_COLORS, "PIN")

xor_y = y1 + CELL_H + 18
lines.append(t(LABEL_X - 6, xor_y + 6, "XOR", size=11, fill=INK, weight="bold", anchor="end"))

y2 = y1 + ROW_GAP
draw_row(y2, pan_field, PAN_GROUPS, PAN_GROUP_COLORS, "PAN")

eq_y = y2 + CELL_H + 18
lines.append(t(LABEL_X - 6, eq_y + 4, "=", size=20, fill=INK, weight="bold", anchor="end"))

y3 = y2 + ROW_GAP
RESULT_GROUPS = [(0, 15, "8-байтовый PIN-блок Format 0 (готов к шифрованию)")]
RESULT_COLOR = {RESULT_GROUPS[0][2]: (WARN, 0.30)}
draw_row(y3, result, RESULT_GROUPS, RESULT_COLOR, "блок")

lines.append("</svg>")

write_svg(figures_dir() / "ch10-cryptography" / "pin-block-format0.svg", lines)
