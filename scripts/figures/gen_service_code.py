"""Генератор service-code.svg для гл. 4, раздел "Сервисный код".

Три позиции сервисного кода Track 2 (iso-7813, Table 3). Каждая позиция
действует независимо. Выделены значения примера 201 из~дампа MTI 0100
(гл. ISO 8583). Раскладка positions_svg() общая с~gen_mti_breakdown.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  CANVAS_H_MAX, CANVAS_W, FONT, FS_BODY, FS_HEAD, FS_NOTE, INK, MUTED, PANEL,
  RX, box, figures_dir, svg_header_pt, text_width, write_svg, xml_escape,
)

POS_1 = [
  ("1", "международная"),
  ("2", "международная + чип"),
  ("5", "национальная"),
  ("6", "национальная + чип"),
  ("7", "частная"),
  ("9", "тестовая"),
]
POS_2 = [
  ("0", "обычная"),
  ("2", "онлайн через эмитента"),
  ("4", "через эмитента, если нет соглашения"),
]
POS_3 = [
  ("0", "без огр., PIN"),
  ("1", "без ограничений"),
  ("2", "товары/услуги"),
  ("3", "ATM, PIN"),
  ("4", "только наличные"),
  ("5", "товары/услуги, PIN"),
  ("6", "без огр., PIN при наличии PED"),
  ("7", "товары/услуги, PIN при PED"),
]

POSITIONS = [
  ("Позиция 1", "interchange + чип", POS_1, "2"),
  ("Позиция 2", "авторизация", POS_2, "0"),
  ("Позиция 3", "услуги + PIN", POS_3, "1"),
]

MARGIN = 2
ROW_H = 12
LINE_H = 9
VAL_X = 5
MEAN_X = 12


def txt(x, y, s, size=FS_BODY, weight="normal", fill=INK, anchor="start"):
  attrs = f' font-size="{size}"'
  if weight != "normal":
    attrs += f' font-weight="{weight}"'
  if fill != INK:
    attrs += f' fill="{fill}"'
  if anchor != "start":
    attrs += f' text-anchor="{anchor}"'
  return f'<text x="{x:g}" y="{y:g}"{attrs}>{xml_escape(s)}</text>'


def wrap(s, width, weight):
  """Перенос по~словам под~ширину width при кегле FS_BODY."""
  lines, cur = [], ""
  for word in s.split():
    cand = f"{cur} {word}".strip()
    if cur and text_width(cand, FS_BODY, weight) > width:
      lines.append(cur)
      cur = word
    else:
      cur = cand
  lines.append(cur)
  return lines


def positions_svg(positions, gap):
  """Колонки позиций: заголовок, цифра примера, список значений.

  positions: [(заголовок, подзаголовок или "", [(значение, смысл)], пример)].
  Строка примера выделена нейтральной плашкой PANEL и~полужирным.
  """
  n = len(positions)
  cw = (CANVAS_W - 2 * MARGIN - (n - 1) * gap) / n
  has_sub = any(p[1] for p in positions)
  y_digit = MARGIN + (22 if has_sub else 14)
  y_head = y_digit + 18 + 11
  y_rows = y_head + 4
  out, bottom = [], 0
  for i, (title, sub, values, example) in enumerate(positions):
    x = MARGIN + i * (cw + gap)
    cx = x + cw / 2
    out.append("<g>")
    out.append(txt(cx, MARGIN + 9, title, FS_HEAD, "bold", anchor="middle"))
    if sub:
      out.append(txt(cx, MARGIN + 18, sub, FS_NOTE, fill=MUTED, anchor="middle"))
    out.append(box(f"{cx - 12:g}", y_digit, 24, 18))
    out.append(txt(cx, y_digit + 12.5, example, FS_HEAD, "bold", anchor="middle"))
    out.append(txt(x + 1, y_head, "Значение · смысл", FS_NOTE, "bold", MUTED))
    out.append("</g>")
    y = y_rows
    for val, meaning in values:
      is_ex = val == example
      weight = "bold" if is_ex else "normal"
      parts = wrap(meaning, cw - MEAN_X - 1, weight)
      h = ROW_H + LINE_H * (len(parts) - 1)
      out.append("<g>")
      if is_ex:
        out.append(
          f'<rect x="{x:g}" y="{y:g}" width="{cw:g}" height="{h}" rx="{RX}" '
          f'fill="{PANEL}"/>'
        )
      out.append(txt(x + VAL_X, y + 9, val, weight=weight, anchor="middle"))
      for k, part in enumerate(parts):
        out.append(txt(x + MEAN_X, y + 9 + k * LINE_H, part, weight=weight))
      out.append("</g>")
      y += h
    bottom = max(bottom, y)
  height = bottom + MARGIN
  if height > CANVAS_H_MAX:
    raise ValueError(f"высота {height} > {CANVAS_H_MAX}")
  lines = svg_header_pt(CANVAS_W, height)
  lines.append(f'<g font-family="{FONT}" fill="{INK}">')
  lines += out
  lines += ["</g>", "</svg>"]
  return lines


if __name__ == "__main__":
  write_svg(figures_dir() / "ch04-card-data" / "service-code.svg",
            positions_svg(POSITIONS, gap=10))
