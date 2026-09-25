"""Жанр bit-map: байты строками, биты 8..1 столбцами, строка примера под сеткой.

Вызывающий gen_*.py описывает байты, подписи битов и~пример:

  write_svg(out, bitgrid(
    rows=["Байт 1", "Байт 2"],
    labels={(0, 7): "SDA", (1, 1): "RFU CL"},
    defined={(0, 7)},
    example=[0x58, 0x00],
  ))

Ячейка определённого бита -- Panel, неопределённого -- Soft с~подписью Muted,
бит примера со~значением 1 -- Warn и~bold (подпись рисунка называет его
жёлтым). notes заменяет двоичную развёртку в~строке примера пояснением.
"""
from _common import (
  CANVAS_W, FONT, FS_BODY, FS_NOTE, INK, MUTED, PANEL, SOFT, SW_FRAME, WARN,
  svg_header_pt, t, text_width,
)

MARGIN = 2
HEAD_H = 20
CELL_H = 18
GAP = 8
EX_H = 22


def _cell(x, y, w, h, fill, opacity=None):
  op = f' fill-opacity="{opacity}"' if opacity else ""
  return (
    f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" '
    f'fill="{fill}"{op} stroke="{MUTED}" stroke-width="{SW_FRAME}"/>'
  )


def _fit(s, width, weight):
  """Кегль 8, при~нехватке ширины 7; не~помещается и~в~7 -- ошибка."""
  for size in (FS_BODY, FS_NOTE):
    if text_width(s, size, weight) <= width - 3:
      return size
  raise ValueError(f"bitgrid: {s!r} шире ячейки ({width:.0f} pt)")


def _is_set(example, row, bit):
  return (example[row] >> (bit - 1)) & 1 == 1


def bitgrid(rows, labels, defined, example, notes=None, width=CANVAS_W):
  label_w = max(text_width(s, FS_BODY, "bold") for s in [*rows, "Пример:"]) + 6
  gx = MARGIN + label_w
  cw = (width - MARGIN - gx) / 8
  out = []

  for col in range(8):
    bit = 8 - col
    cx = gx + col * cw + cw / 2
    out.append(t(f"{cx:.1f}", 9, f"бит {bit}", size=FS_NOTE, weight="bold",
                 fill=MUTED))
    if bit in (8, 1):
      out.append(t(f"{cx:.1f}", 17, "MSB" if bit == 8 else "LSB",
                   size=FS_NOTE, fill=MUTED))

  y = HEAD_H
  for row, name in enumerate(rows):
    out.append(t(f"{gx - 6:.1f}", y + 12, name, size=FS_BODY, weight="bold",
                 anchor="end"))
    for col in range(8):
      bit = 8 - col
      x = gx + col * cw
      is_def = (row, bit) in defined
      hit = is_def and _is_set(example, row, bit)
      if hit:
        out.append(_cell(x, y, cw, CELL_H, WARN, 0.18))
      else:
        out.append(_cell(x, y, cw, CELL_H, PANEL if is_def else SOFT))
      s = labels.get((row, bit))
      if s:
        weight = "bold" if hit else "normal"
        size = _fit(s, cw, weight)
        out.append(t(f"{x + cw / 2:.1f}", y + 12, s, size=size, weight=weight,
                     fill=INK if is_def else MUTED))
    y += CELL_H

  y += GAP
  out.append(t(f"{gx - 6:.1f}", y + 14, "Пример:", size=FS_BODY,
               weight="bold", fill=MUTED, anchor="end"))
  bw = (width - MARGIN - gx) / len(example)
  for i, byte in enumerate(example):
    x = gx + i * bw
    hit = any((i, b) in defined and _is_set(example, i, b) for b in range(1, 9))
    out.append(_cell(x + 1, y, bw - 2, EX_H, WARN if hit else SOFT,
                     0.18 if hit else None))
    out.append(t(f"{x + bw / 2:.1f}", y + 9, f"0x{byte:02X}", size=FS_BODY,
                 weight="bold" if hit else "normal"))
    if notes:
      sub = notes[i]
    else:
      b = f"{byte:08b}"
      sub = f"{b[:4]} {b[4:]}"
    _fit(sub, bw - 2, "normal")
    out.append(t(f"{x + bw / 2:.1f}", y + 18, sub, size=FS_NOTE, fill=MUTED))
  height = y + EX_H + MARGIN

  return svg_header_pt(width, height) + [
    f'<g font-family="{FONT}">'
  ] + out + ["</g>", "</svg>"]
