"""Генератор pin-block-format0.svg для гл. 10 § 10.5.

ISO 9564 Format 0 -- 8-байтовый PIN-блок, XOR двух 16-ниббловых полей:
- PIN-поле: [0][len][PIN digits][F-padding]
- PAN-поле: [0000][rightmost 12 of PAN без check digit]

Пример: PIN=1234, тестовый PAN Stripe 4242 4242 4242 4242.
Источники: iso-9564, stripe-testing.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  ACCENT_A, ACCENT_B, CANVAS_W, FS_BODY, FS_HEAD, FS_NOTE, INK, MUTED,
  PANEL, SOFT, SW_FRAME, TIER_DARK, TIER_LIGHT_MID, TIER_NEUTRAL,
  figures_dir, svg_header_pt, t, text_width, write_svg,
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

LEFT_PAD = 33
CELL_W = (CANVAS_W - LEFT_PAD - 2) / 16
CELL_H = 16
ROW_GAP = 36
LABEL_X = LEFT_PAD - 5
ROW_Y_START = 32

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
RESULT_GROUPS = [(0, 15, "8-байтовый PIN-блок Format 0 (готов к шифрованию)")]

# Операнды XOR разведены по тирам светлоты (светлый PIN, тёмный PAN),
# результат -- нейтральный тёмный тир: при равной opacity 0.15 оттенки
# сливаются, особенно при дальтонизме.
PIN_GROUP_COLORS = {
  "формат": (PANEL, 1.0),
  "длина": (PANEL, 1.0),
  "PIN": (ACCENT_A, TIER_LIGHT_MID),
  "F-padding": (SOFT, 1.0),
}
PAN_GROUP_COLORS = {
  "нули": (SOFT, 1.0),
  "правые 12 цифр PAN без check": (ACCENT_B, TIER_DARK),
}
RESULT_COLOR = {RESULT_GROUPS[0][2]: (MUTED, TIER_NEUTRAL)}


def group_color_for(nibble_idx, groups, color_map):
  for start, end, label in groups:
    if start <= nibble_idx <= end:
      return color_map[label]
  return (SOFT, 1.0)


VIEW_H = ROW_Y_START + 2 * ROW_GAP + CELL_H + 2
lines = svg_header_pt(CANVAS_W, VIEW_H)

lines.append(t(LEFT_PAD, 9, "Вход:", size=FS_BODY, fill=MUTED, weight="bold",
               anchor="start"))
lines.append(t(LEFT_PAD + 28, 9,
               f"PIN = {PIN}; PAN = {PAN_FULL} (check digit = {PAN_FULL[-1]})",
               size=FS_BODY, fill=INK, anchor="start"))


def draw_row(y, nibbles, groups, color_map, row_label):
  lines.append("<g>")
  lines.append(t(LABEL_X, y + 11, row_label, size=FS_BODY, fill=MUTED,
                 weight="bold", anchor="end"))
  for start, end, lbl in groups:
    center_x = LEFT_PAD + (start + (end - start) / 2 + 0.5) * CELL_W
    span = (end - start + 1) * CELL_W
    # Подпись шире одиночной ячейки поднимается на строку: соседние
    # однониббловые группы (формат, длина) иначе сталкиваются подписями.
    dy = 3 if text_width(lbl, FS_NOTE) < span else 10
    lines.append(t(f"{center_x:.2f}", y - dy, lbl, size=FS_NOTE, fill=MUTED))
  for i, nib in enumerate(nibbles):
    cx = LEFT_PAD + i * CELL_W
    fill, opacity = group_color_for(i, groups, color_map)
    op = f' fill-opacity="{opacity}"' if opacity != 1.0 else ""
    lines.append(
      f'<rect x="{cx:.2f}" y="{y}" width="{CELL_W - 1:.2f}" height="{CELL_H}" '
      f'fill="{fill}"{op} stroke="{MUTED}" stroke-width="{SW_FRAME}"/>'
    )
    lines.append(t(f"{cx + (CELL_W - 1) / 2:.2f}", y + 11, nib, size=FS_BODY,
                   fill=INK, weight="bold"))
  lines.append("</g>")


y1 = ROW_Y_START
draw_row(y1, pin_field, PIN_GROUPS, PIN_GROUP_COLORS, "PIN")
lines.append(t(LABEL_X, y1 + CELL_H + 13, "XOR", size=FS_HEAD, fill=INK,
               weight="bold", anchor="end"))

y2 = y1 + ROW_GAP
draw_row(y2, pan_field, PAN_GROUPS, PAN_GROUP_COLORS, "PAN")
lines.append(t(LABEL_X, y2 + CELL_H + 13, "=", size=FS_HEAD, fill=INK,
               weight="bold", anchor="end"))

y3 = y2 + ROW_GAP
draw_row(y3, result, RESULT_GROUPS, RESULT_COLOR, "блок")

lines.append("</svg>")

write_svg(figures_dir() / "ch10-cryptography" / "pin-block-format0.svg", lines)
