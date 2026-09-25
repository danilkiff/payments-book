"""Генератор secure-messaging.svg для гл. 10 (Secure Messaging EMV).

Защищённая команда эмитента (issuer script) = тег команды 86 + заголовок
APDU (CLA INS P1 P2) + данные + MAC. MAC считается на сессионном ключе
SK_SMI поверх заголовка и данных (целостность и аутентичность); при
необходимости данные шифруются на SK_SMC (конфиденциальность, например
новый PIN в PIN CHANGE). Источник: emvco-book2, §9.

AccentA помечает всё, что относится к ключу SK_SMI (MAC и его охват),
AccentB -- к ключу SK_SMC (шифр данных).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  ACCENT_A, CANVAS_W, FS_BODY, FS_NOTE, MUTED, SW_LINK,
  box, figures_dir, svg_header_pt, t, text_width, write_svg,
)

# (верхняя подпись, нижняя подпись, ширина, тон)
BOXES = [
  ("86", "тег команды", 52, None),
  ("CLA INS P1 P2", "заголовок APDU", 118, None),
  ("данные", "шифр на SK_SMC", 110, "AccentB"),
  ("MAC", "на SK_SMI", 70, "AccentA"),
]

GAP = 6
BOX_H = 20
STRIP_Y = 2
total = sum(b[2] for b in BOXES) + GAP * (len(BOXES) - 1)
STRIP_X = (CANVAS_W - total) / 2
LBL_Y = STRIP_Y + BOX_H + 10
BRACKET_Y = LBL_Y + 10
VIEW_H = BRACKET_Y + 14

lines = svg_header_pt(CANVAS_W, VIEW_H)

x = STRIP_X
box_x = {}
for top, bottom, w, tone in BOXES:
  for s, size, weight in ((top, FS_BODY, "bold"), (bottom, FS_NOTE, "normal")):
    assert text_width(s, size, weight) < w + GAP, s
  lines.append("<g>")
  lines.append(box(x, STRIP_Y, w, BOX_H, tone))
  lines.append(t(x + w / 2, STRIP_Y + 13.5, top, size=FS_BODY, weight="bold"))
  lines.append(t(x + w / 2, LBL_Y, bottom, size=FS_NOTE, fill=MUTED))
  lines.append("</g>")
  box_x[top] = (x, w)
  x += w + GAP

# Скобка охвата MAC: от начала заголовка до конца данных
hx0 = box_x["CLA INS P1 P2"][0]
hx1 = box_x["данные"][0] + box_x["данные"][1]
by = BRACKET_Y
lines.append("<g>")
lines.append(
  f'<path d="M{hx0} {by - 5} L{hx0} {by} L{hx1} {by} L{hx1} {by - 5}" '
  f'fill="none" stroke="{ACCENT_A}" stroke-width="{SW_LINK}"/>'
)
lines.append(t((hx0 + hx1) / 2, by + 10, "входит в MAC", size=FS_NOTE,
               fill=ACCENT_A))
lines.append("</g>")

lines.append("</svg>")
write_svg(figures_dir() / "ch10-cryptography" / "secure-messaging.svg", lines)
