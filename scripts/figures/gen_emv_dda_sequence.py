"""Генератор emv-dda-sequence.svg для гл. 7 EMV (контактный DDA).

Терминал читает записи и~сертификаты, восстанавливает цепочку PKI
(CA -> эмитент -> ICC), передаёт карте непредсказуемое число (тег 9F37)
по~DDOL в~INTERNAL AUTHENTICATE; карта возвращает SDAD (тег 9F4B),
терминал проверяет подпись.
Источник: emvco-book2, emv-tag-9F4C.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
  CANVAS_H_MAX, CANVAS_W, FS_NOTE, box, figures_dir, t, write_svg,
)
from _seq import Act, Msg, Party, Phase, sequence

PARTIES = [
  Party("term", "Терминал", side="AccentA"),
  Party("card", "Карта", side="AccentB"),
]

EVENTS = [
  Phase("PRE INTERNAL AUTHENTICATE"),
  Msg("term", "card", "READ RECORD", strong=True),
  Msg("card", "term", "записи EMV + сертификаты", reply=True),
  Act("term", "PKI: PK CA → эмитент → ICC"),
  Phase("INTERNAL AUTHENTICATE"),
  Act("term", "UN = rand(4B), тег 9F37"),
  Msg("term", "card", "INTERNAL AUTHENTICATE", strong=True, note="UN + DDOL"),
  Act("card", "формирует SDAD"),
  Msg("card", "term", "SDAD", reply=True, strong=True, note="тег 9F4B"),
  Phase("VERIFY"),
]

# Исходы проверки под диаграммой (альтернативы, рядом): _seq их не рисует, блоки добавляются здесь.
OUTCOMES = [
  ("SDAD проверен → DDA", "Good"),
  ("подпись/hash не совпали → отказ", "Bad"),
]
OUT_H = 14
OUT_GAP = 4


def build():
  lines = sequence(PARTIES, EVENTS)
  svg_i = next(i for i, s in enumerate(lines) if s.startswith("<svg "))
  h0 = float(lines[svg_i].split('viewBox="0 0 ')[1].split('"')[0].split()[1])
  y = h0 + OUT_GAP
  bw = (CANVAS_W - 4 - OUT_GAP) / 2
  extra = []
  for i, (label, tone) in enumerate(OUTCOMES):
    x = 2 + i * (bw + OUT_GAP)
    extra += [
      "<g>",
      box(f"{x:.1f}", f"{y:.1f}", f"{bw:.1f}", OUT_H, tone),
      t(f"{x + bw / 2:.1f}", f"{y + 10:.1f}", label, size=FS_NOTE, weight="bold"),
      "</g>",
    ]
  h = round(y + OUT_H + 2, 1)
  if h > CANVAS_H_MAX:
    raise ValueError(f"высота {h} > {CANVAS_H_MAX}")
  lines[svg_i] = (
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {h:g}" '
    f'width="{CANVAS_W}pt" height="{h:g}pt">'
  )
  return lines[:-1] + extra + ["</svg>"]


if __name__ == "__main__":
  write_svg(figures_dir() / "ch07-emv" / "emv-dda-sequence.svg", build())
