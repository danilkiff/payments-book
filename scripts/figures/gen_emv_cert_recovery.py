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
  CANVAS_W, FONT, FS_BODY, FS_NOTE, MUTED, box, figures_dir, svg_header_pt, t,
  write_svg,
)

# (верхняя подпись, нижняя подпись, ширина, тон). Маркеры и формат --
# нейтральный Panel; поля сертификата и хеш -- два типа данных (A, B).
BOXES = [
  ("6A", "заголовок", 38, None),
  ("02", "формат", 38, None),
  ("поля + ключ эмитента", "ID, срок, серийный, PK", 150, "AccentA"),
  ("Hash", "SHA-1, 20 байт", 90, "AccentB"),
  ("BC", "трейлер", 38, None),
]

W = CANVAS_W
GAP = 5
BOX_H = 18
STRIP_W = sum(b[2] for b in BOXES) + GAP * (len(BOXES) - 1)
X0 = (W - STRIP_W) / 2
Y0 = 2
NOTE_Y = Y0 + BOX_H + 21
H = NOTE_Y + 3


def build():
  out = []
  x = X0
  for top, bottom, w, tone in BOXES:
    out += [
      "<g>",
      box(f"{x:.1f}", Y0, w, BOX_H, tone),
      t(f"{x + w / 2:.1f}", Y0 + 12, top, size=FS_BODY, weight="bold"),
      t(f"{x + w / 2:.1f}", Y0 + BOX_H + 9, bottom, size=FS_NOTE, fill=MUTED),
      "</g>",
    ]
    x += w + GAP
  out.append(t(f"{X0:.1f}", NOTE_Y,
               "открытый ключ CA восстанавливает блок; терминал сверяет Hash",
               size=FS_NOTE, fill=MUTED, anchor="start"))
  return svg_header_pt(W, H) + [f'<g font-family="{FONT}">'] + out + ["</g>", "</svg>"]


if __name__ == "__main__":
  write_svg(figures_dir() / "ch07-emv" / "emv-cert-recovery.svg", build())
