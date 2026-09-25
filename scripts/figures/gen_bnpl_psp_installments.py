"""Генератор bnpl-psp-installments.svg для гл. 22 (BNPL, сбор взносов Pay-in-4).

Маркировка CIT/MIT и~связка NTID / Trace ID -- mrc-nti-trace-id.
Колонки момента списания и~маркера авторизации _seq.py не~даёт: sequence
верстается в~средней полосе и~сдвигается, колонки рисуются здесь по~тем же
шагам строки (_seq.HEAD_H, _seq.ROW).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _seq
from _common import (
  CANVAS_W, FS_BODY, FS_NOTE, MUTED, figures_dir, svg_header_pt, t,
  text_width, write_svg,
)
from _seq import Msg, Party, sequence

PARTIES = [
  Party("cli", "Клиент", side="AccentA"),
  Party("bnpl", "BNPL-провайдер", side="AccentB"),
]

# момент, доля, маркер авторизации, ссылка на~первичную операцию
ROWS = [
  ("T0", "1/4", "CIT", ""),
  ("T+14 дн", "2/4", "MIT", "NTID / Trace ID ref"),
  ("T+28 дн", "3/4", "MIT", "NTID / Trace ID ref"),
  ("T+42 дн", "4/4", "MIT", "NTID / Trace ID ref"),
]

LEFT = 48
RIGHT = 96
MID = CANVAS_W - LEFT - RIGHT


def build():
  events = [Msg("bnpl", "cli", f"списание {part} (25 %)") for _, part, _, _ in ROWS]
  seq = sequence(PARTIES, events, width=MID)
  header, body = seq[1], seq[2:-1]
  height = float(header.split('viewBox="')[1].split('"')[0].split()[3])
  defs = body.pop(0)[len("<defs>"):-len("</defs>")]

  out = svg_header_pt(CANVAS_W, height + 2, defs)
  out.append(f'<g transform="translate({LEFT},0)">')
  out += body
  out.append("</g>")

  xl, xr = 2, LEFT + MID + 4
  out.append(t(xl, 11, "момент", size=FS_NOTE, weight="bold", fill=MUTED, anchor="start"))
  out.append(t(xl, 19, "/ доля", size=FS_NOTE, fill=MUTED, anchor="start"))
  out.append(t(xr, 11, "маркер", size=FS_NOTE, weight="bold", fill=MUTED, anchor="start"))
  out.append(t(xr, 19, "авторизации", size=FS_NOTE, fill=MUTED, anchor="start"))

  y = _seq.HEAD_H + 6
  for moment, _, mark, ref in ROWS:
    y += _seq.ROW
    out.append(t(xl, y + 3, moment, size=FS_BODY, weight="bold", anchor="start"))
    x = xr
    out.append(t(x, y + 3, mark, size=FS_BODY, weight="bold", anchor="start"))
    if ref:
      x += text_width(mark, FS_BODY, "bold") + 4
      out.append(t(f"{x:.1f}", y + 3, ref, size=FS_NOTE, fill=MUTED, anchor="start"))
      if x + text_width(ref, FS_NOTE) > CANVAS_W - 2:
        raise ValueError("колонка маркера шире холста")
  out.append("</svg>")
  return out


if __name__ == "__main__":
  out = figures_dir() / "ch22-bnpl" / "bnpl-psp-installments.svg"
  write_svg(out, build())
