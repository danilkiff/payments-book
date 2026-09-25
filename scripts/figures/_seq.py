"""Жанр sequence: участники по~горизонтали, время сверху вниз.

Вызывающий gen_*.py описывает участников и~события, вёрстку делает sequence():

  P = [Party("snd", "Отправитель", "мобильный банк", side="AccentA"), ...]
  E = [
    Msg("snd", "bank", "номер телефона"),
    Msg("opkc", "bank", "ответ", reply=True),
    Msg("bank", "opkc", "выбор банка", strong=True, note="пояснение"),
    Act("opkc", "расчёт ПС БР"),
    Phase("Расчёт и подтверждение"),
  ]
  write_svg(out, sequence(P, E))

side участника (AccentA / AccentB) различает две стороны сценария; остальные
участники нейтральны. tone сообщения (Good / Warn / Bad) -- только оценка
исхода; по~умолчанию сообщение Muted, ответ -- пунктир.
"""
from dataclasses import dataclass

from _common import (
  CANVAS_H_MAX, CANVAS_W, FS_BODY, FS_NOTE, INK, MUTED, PANEL, SW_FRAME,
  DASH, arrow, box, markers, svg_header_pt, t, text_width,
)


@dataclass
class Party:
  key: str
  title: str
  sub: str = ""
  side: str | None = None


@dataclass
class Msg:
  src: str
  dst: str
  label: str
  reply: bool = False
  tone: str = "Muted"
  strong: bool = False
  note: str = ""


@dataclass
class Act:
  at: str
  label: str


@dataclass
class Phase:
  label: str


MARGIN = 2
HEAD_H = 24
ROW = 17
NOTE_ROW = 8
ACT_H = 13
PHASE_ROW = 15
TAIL = 6


def _label(cx, y, s, size, weight, fill):
  """Подпись с~белой подложкой: линии жизни не~пересекают текст."""
  w = text_width(s, size, weight) + 4
  h = size + 1
  return [
    f'<rect x="{cx - w / 2:.1f}" y="{y - size + 0.5:.1f}" width="{w:.1f}" '
    f'height="{h}" fill="#ffffff"/>',
    t(f"{cx:.1f}", f"{y:.1f}", s, size=size, weight=weight, fill=fill),
  ]


def _rows(p):
  rows = [(s, FS_BODY, "bold", INK) for s in p.title.split("\n")]
  rows += [(s, FS_NOTE, "normal", MUTED) for s in p.sub.split("\n") if s]
  return rows


def sequence(parties, events, width=CANVAS_W, lanes=None):
  """lanes -- ширины полос участников в~pt; по~умолчанию полосы равные.

  Перевод строки в~title и~sub участника даёт многострочную шапку.
  """
  inner = width - 2 * MARGIN
  lanes = lanes or [inner / len(parties)] * len(parties)
  if len(lanes) != len(parties) or sum(lanes) > inner + 0.01:
    raise ValueError(f"sequence: полосы {lanes} не~укладываются в~{inner} pt")
  cx, bw = {}, {}
  x0 = MARGIN + (inner - sum(lanes)) / 2
  for p, w in zip(parties, lanes):
    cx[p.key], bw[p.key] = x0 + w / 2, w - 6
    x0 += w
  head_h = max(HEAD_H, *(MARGIN + 9 * len(_rows(p)) + 4 for p in parties))

  body = []
  y = head_h + 6
  for ev in events:
    if isinstance(ev, Msg):
      y += ROW
      x1, x2 = cx[ev.src], cx[ev.dst]
      d = 1 if x2 > x1 else -1
      body.append(arrow(f"{x1:.1f}", y, f"{x2 - d:.1f}", y, ev.tone, ev.reply))
      weight = "bold" if ev.strong else "normal"
      body += _label((x1 + x2) / 2, y - 3, ev.label, FS_BODY, weight, INK)
      if ev.note:
        y += NOTE_ROW
        body += _label((x1 + x2) / 2, y, ev.note, FS_NOTE, "normal", MUTED)
    elif isinstance(ev, Act):
      y += 5
      w = text_width(ev.label, FS_NOTE, "bold") + 10
      x = cx[ev.at] - w / 2
      body.append(box(f"{x:.1f}", y, f"{w:.1f}", ACT_H, None, dashed=True))
      body.append(
        t(f"{cx[ev.at]:.1f}", y + 9, ev.label, size=FS_NOTE, weight="bold")
      )
      y += ACT_H
    elif isinstance(ev, Phase):
      y += PHASE_ROW
      body.append(
        f'<rect x="{MARGIN}" y="{y - 9}" width="{width - 2 * MARGIN}" '
        f'height="12" fill="{PANEL}"/>'
      )
      body.append(
        t(MARGIN + 4, y, ev.label, size=FS_NOTE, weight="bold", fill=MUTED,
          anchor="start")
      )
  height = y + TAIL
  if height > CANVAS_H_MAX:
    raise ValueError(f"sequence: высота {height} > {CANVAS_H_MAX}, делить фигуру")

  head = []
  for p in parties:
    x = cx[p.key]
    head.append(box(f"{x - bw[p.key] / 2:.1f}", MARGIN, f"{bw[p.key]:.1f}", head_h - MARGIN, p.side))
    rows = _rows(p)
    ty = MARGIN + (head_h - MARGIN - 9 * len(rows)) / 2 + 7
    for j, (s, size, weight, fill) in enumerate(rows):
      head.append(t(f"{x:.1f}", f"{ty + 9 * j:.1f}", s, size=size, weight=weight, fill=fill))
      if text_width(s, size, weight) > bw[p.key] - 4:
        raise ValueError(f"sequence: {s!r} шире шапки участника ({bw[p.key]:.0f} pt)")
    head.append(
      f'<line x1="{x:.1f}" y1="{head_h}" x2="{x:.1f}" y2="{height}" '
      f'stroke="{MUTED}" stroke-width="{SW_FRAME}" stroke-dasharray="{DASH}"/>'
    )

  tones = sorted({ev.tone for ev in events if isinstance(ev, Msg)})
  return svg_header_pt(width, height, markers(*tones)) + head + body + ["</svg>"]
