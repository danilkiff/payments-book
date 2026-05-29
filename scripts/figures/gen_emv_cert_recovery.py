"""Генератор emv-cert-recovery.svg для гл. 7 EMV (подпись с восстановлением).

EMV-подпись по ISO/IEC 9796-2 (Book 2, Annex A2.1): терминал возводит
сертификат в степень открытого ключа CA и восстанавливает данные, обрамлённые
маркерами 6A (заголовок) и BC (трейлер); между ними -- поля сертификата и хеш
SHA-1, который терминал пересчитывает и сверяет.
Источник: emvco-book2, §5.3.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, ACCENT_A, ACCENT_B, WARN,
  figures_dir, t, write_svg, svg_header,
)

# (верхняя подпись, нижняя подпись, ширина, цвет)
BOXES = [
  ("6A", "заголовок", 50, WARN),
  ("02", "формат", 50, MUTED),
  ("поля + ключ эмитента", "ID, срок, серийный, PK", 210, ACCENT_A),
  ("Hash", "SHA-1, 20 байт", 110, ACCENT_B),
  ("BC", "трейлер", 50, WARN),
]

VIEW_W = 548
STRIP_X = 12
STRIP_Y = 22
BOX_H = 30
GAP = 6
NOTE_Y = STRIP_Y + BOX_H + 16 + 18
VIEW_H = NOTE_Y + 14

lines = svg_header(VIEW_W, VIEW_H)

x = STRIP_X
for top, bottom, w, color in BOXES:
  lines.append(
    f'<rect x="{x}" y="{STRIP_Y}" width="{w}" height="{BOX_H}" '
    f'fill="{color}" fill-opacity="0.16" stroke="{MUTED}" stroke-width="0.5"/>'
  )
  size = 11 if len(top) <= 6 else 10
  lines.append(t(x + w / 2, STRIP_Y + 20, top, size=size, fill=INK, weight="bold"))
  lines.append(t(x + w / 2, STRIP_Y + BOX_H + 13, bottom, size=9, fill=MUTED))
  x += w + GAP

lines.append(t(STRIP_X, NOTE_Y, "открытый ключ CA восстанавливает блок; терминал сверяет Hash",
               size=9, fill=MUTED, anchor="start"))

lines.append("</svg>")
write_svg(figures_dir() / "ch07-emv" / "emv-cert-recovery.svg", lines)
