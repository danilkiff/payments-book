"""Генератор card-personalization-flow.svg для гл. 7 EMV.

Конвейер выпуска карты: эмитент готовит данные и ключи -> центр подготовки
данных формирует файл персонализации (шифруя секреты под транспортным ключом)
-> бюро персонализации записывает их в чип по защищённому каналу GlobalPlatform
-> карта получает апплет, ключи, счётчики и CPLC.
Источник: emvco-cps, globalplatform-card, visa-vsdc-guide.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  INK, MUTED, ACCENT_A, ACCENT_B,
  figures_dir, t, write_svg, svg_header,
)

# (заголовок, строка 1, строка 2, цвет)
STAGES = [
  ("Эмитент", "данные, ключи,", "сертификаты", ACCENT_A),
  ("Подготовка данных", "файл персонализации,", "зашифровано под ZCMK", ACCENT_B),
  ("Бюро персонализации", "запись в чип", "по каналу GlobalPlatform", ACCENT_A),
  ("Карта", "апплет, ключи,", "счётчики, CPLC", ACCENT_B),
]

VIEW_W = 636
BOX_W = 132
BOX_H = 58
GAP = 28
BOX_X0 = 12
BOX_Y = 22

NOTE_Y = BOX_Y + BOX_H + 26
VIEW_H = NOTE_Y + 14

MARKER = (
  '<marker id="arr" markerWidth="9" markerHeight="9" refX="6" refY="3" '
  f'orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{MUTED}"/></marker>'
)
lines = svg_header(VIEW_W, VIEW_H, extra_defs=MARKER)

centers = []
for i, (title, l1, l2, color) in enumerate(STAGES):
  x = BOX_X0 + i * (BOX_W + GAP)
  lines.append(
    f'<rect x="{x}" y="{BOX_Y}" width="{BOX_W}" height="{BOX_H}" rx="4" '
    f'fill="{color}" fill-opacity="0.13" stroke="{MUTED}" stroke-width="0.6"/>'
  )
  lines.append(t(x + BOX_W / 2, BOX_Y + 20, title, size=11, fill=INK, weight="bold"))
  lines.append(t(x + BOX_W / 2, BOX_Y + 37, l1, size=9, fill=MUTED))
  lines.append(t(x + BOX_W / 2, BOX_Y + 50, l2, size=9, fill=MUTED))
  centers.append((x, x + BOX_W))

# Стрелки между стадиями
ay = BOX_Y + BOX_H / 2
for i in range(len(STAGES) - 1):
  x1 = centers[i][1] + 3
  x2 = centers[i + 1][0] - 3
  lines.append(
    f'<line x1="{x1}" y1="{ay}" x2="{x2 - 4}" y2="{ay}" '
    f'stroke="{MUTED}" stroke-width="1.2" marker-end="url(#arr)"/>'
  )

lines.append(t(BOX_X0, NOTE_Y,
               "секреты защищены транспортным ключом (ZCMK); загрузка под dual control и split knowledge",
               size=9, fill=MUTED, anchor="start"))

lines.append("</svg>")
write_svg(figures_dir() / "ch07-emv" / "card-personalization-flow.svg", lines)
