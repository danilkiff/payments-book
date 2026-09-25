"""Генератор card-personalization-flow.svg для гл. 7 EMV.

Верх: производитель и~эмитент передают ключевой материал бюро
персонализации под~транспортным ключом TK, бюро записывает апплет и~ключи
в~чип по~каналу GlobalPlatform SCP02/03. Низ: TK собирают XOR двух
компонентов кастодианов (dual control, split knowledge); по~назначению TK --
KEK, DEK, PEK.
Производитель и~эмитент -- две стороны обмена (AccentB, AccentA), остальные
блоки нейтральны.
Источник: emvco-cps, globalplatform-card, visa-vsdc-guide.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  CANVAS_W, FONT, FS_BODY, FS_HEAD, FS_NOTE, MUTED, SOFT, SW_BOX, SW_FRAME,
  DASH, arrow, box, figures_dir, markers, svg_header_pt, t, write_svg,
)

W = CANVAS_W


def block(x, y, w, h, title, lines=(), tone=None):
  """Блок: имя 8 bold, под ним строки 7 Muted; текст центрируется по~высоте."""
  out = ["<g>", box(x, y, w, h, tone)]
  total = 8 + 8 * len(lines)
  ty = y + (h - total) / 2 + 7
  out.append(t(x + w / 2, f"{ty:.1f}", title, size=FS_BODY, weight="bold"))
  for i, s in enumerate(lines):
    out.append(t(x + w / 2, f"{ty + 9 * (i + 1):.1f}", s, size=FS_NOTE,
                 fill=MUTED))
  out.append("</g>")
  return out


def build():
  out = []
  # Верх: межзональный обмен.
  out += block(2, 4, 104, 24, "Производитель", ["кристалл, предперсо-ключ"],
               "AccentB")
  out += block(2, 48, 104, 24, "Эмитент", ["IMK → UDK, перс. файл"], "AccentA")
  out += block(144, 21, 118, 34, "Бюро персонализации",
               ["пишет апплет,", "секретов не видит открытыми"])
  out += block(320, 26, 63, 24, "Карта", ["апплет, ключи"])
  out += ["<g>", arrow(107, 16, 143, 31, "AccentB"),
          t(124, 18, "TK", size=FS_NOTE, weight="bold", fill=MUTED), "</g>"]
  out += ["<g>", arrow(107, 60, 143, 45, "AccentA"),
          t(124, 63, "TK", size=FS_NOTE, weight="bold", fill=MUTED), "</g>"]
  out += ["<g>", arrow(263, 38, 319, 38),
          t(291, 34, "GP SCP02/03", size=FS_NOTE, fill=MUTED), "</g>"]

  # Низ: сборка транспортного ключа.
  zy = 84
  out += [
    "<g>",
    f'<rect x="2" y="{zy}" width="{W - 4}" height="86" rx="3" fill="{SOFT}" '
    f'stroke="{MUTED}" stroke-width="{SW_FRAME}" stroke-dasharray="{DASH}"/>',
    t(10, zy + 13, "Транспортный ключ (TK) под dual control и split knowledge",
      size=FS_HEAD, weight="bold", anchor="start"),
    "</g>",
  ]
  out += block(14, zy + 24, 84, 24, "Кастодиан 1", ["компонент A"])
  out += block(14, zy + 54, 84, 24, "Кастодиан 2", ["компонент B"])
  cx, cy, r = 150, zy + 51, 13
  out += [
    "<g>",
    f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#ffffff" stroke="{MUTED}" '
    f'stroke-width="{SW_BOX}"/>',
    t(cx, cy + 3, "XOR", size=FS_BODY, weight="bold"),
    "</g>",
  ]
  out.append(arrow(99, zy + 38, cx - r - 1, cy - 4))
  out.append(arrow(99, zy + 64, cx - r - 1, cy + 4))
  out += block(206, zy + 39, 110, 24, "Транспортный ключ", ["KEK · DEK · PEK"])
  out.append(arrow(cx + r, cy, 205, cy))
  out.append(t(261, zy + 76, "ни один оператор не видит ключ целиком",
               size=FS_NOTE, fill=MUTED))

  h = zy + 88
  return (svg_header_pt(W, h, markers("AccentA", "AccentB", "Muted"))
          + [f'<g font-family="{FONT}" fill="#1A2030">'] + out + ["</g>", "</svg>"])


if __name__ == "__main__":
  write_svg(figures_dir() / "ch07-emv" / "card-personalization-flow.svg", build())
