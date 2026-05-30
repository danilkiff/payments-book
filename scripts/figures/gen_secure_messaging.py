"""Генератор secure-messaging.svg для гл. 10 (Secure Messaging EMV).

Защищённая команда эмитента (issuer script) = тег команды 86 + заголовок
APDU (CLA INS P1 P2) + данные + MAC. MAC считается на сессионном ключе
SK_SMI поверх заголовка и данных (целостность и аутентичность); при
необходимости данные шифруются на SK_SMC (конфиденциальность, например
новый PIN в PIN CHANGE). Источник: emvco-book2, §9.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, SOFT, ACCENT_A, ACCENT_B, WARN,
  figures_dir, t, write_svg, svg_header,
)

# (верхняя подпись, нижняя подпись, ширина, цвет)
BOXES = [
  ("86", "тег команды", 56, MUTED),
  ("CLA INS P1 P2", "заголовок APDU", 150, ACCENT_A),
  ("данные", "шифр на SK_SMC", 130, ACCENT_B),
  ("MAC", "на SK_SMI", 90, WARN),
]

VIEW_W = 520
STRIP_X = 12
STRIP_Y = 22
BOX_H = 30
GAP = 6
LBL_BELOW = 16
BRACKET_Y = STRIP_Y + BOX_H + LBL_BELOW + 16
VIEW_H = BRACKET_Y + 30

lines = svg_header(VIEW_W, VIEW_H)

x = STRIP_X
box_x = {}
for top, bottom, w, color in BOXES:
  # Warn (жёлтый) на белом фоне иначе пропадает -- канон требует 0.18.
  fill_opacity = {WARN: "0.18"}.get(color, "0.15")
  lines.append(
    f'<rect x="{x}" y="{STRIP_Y}" width="{w}" height="{BOX_H}" '
    f'fill="{color}" fill-opacity="{fill_opacity}" stroke="{MUTED}" stroke-width="0.5"/>'
  )
  lines.append(t(x + w / 2, STRIP_Y + 20, top, size=11, fill=INK, weight="bold"))
  lines.append(t(x + w / 2, STRIP_Y + BOX_H + 13, bottom, size=9, fill=MUTED))
  box_x[top] = (x, w)
  x += w + GAP

# Скобка «под MAC»: от начала заголовка до конца данных
hx0 = box_x["CLA INS P1 P2"][0]
hx1 = box_x["данные"][0] + box_x["данные"][1]
by = BRACKET_Y
lines.append(
  f'<path d="M{hx0} {by - 6} L{hx0} {by} L{hx1} {by} L{hx1} {by - 6}" '
  f'fill="none" stroke="{WARN}" stroke-width="1"/>'
)
lines.append(t((hx0 + hx1) / 2, by + 14, "входит в MAC", size=9, fill=WARN))

lines.append("</svg>")
write_svg(figures_dir() / "ch10-cryptography" / "secure-messaging.svg", lines)
