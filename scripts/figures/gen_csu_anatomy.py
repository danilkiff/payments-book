"""Генератор csu-anatomy.svg для гл. 7 EMV (CSU, ответ эмитента карте).

CSU (Card Status Update) -- 4 байта внутри Issuer Authentication Data (тег 91)
рядом с ARPC. Инструктирует чип после онлайн-ответа: одобрение, блокировка
карты/приложения, обновление счётчика попыток PIN, признак «онлайн в след. раз»,
обновление офлайн-счётчиков (2 бита). Байт 1 -- нибл PTC; байт 3 RFU; байт 4 --
ID профилей сброса счётчиков.
Пример: CSU = 0x00 82 00 00 -- эмитент одобряет и сбрасывает офлайн-счётчики.
Источник: emvco-book3, Table CCD 11.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bitgrid import bitgrid
from _common import figures_dir, write_svg

LABELS = {
  (0, 8): "пропр.", (0, 4): "PTC",
  (1, 8): "одобр.", (1, 7): "карта✗", (1, 6): "прил.✗", (1, 5): "обн.PTC",
  (1, 4): "онл.след", (1, 3): "proxy", (1, 2): "счётч.",
  (3, 8): "профиль 1", (3, 4): "профиль 2",
}
DEFINED = {
  (0, 8), (0, 4), (0, 3), (0, 2), (0, 1),
  (1, 8), (1, 7), (1, 6), (1, 5), (1, 4), (1, 3), (1, 2), (1, 1),
  (3, 8), (3, 7), (3, 6), (3, 5), (3, 4), (3, 3), (3, 2), (3, 1),
}
ROWS = ["1: PTC", "2: действия", "3: RFU", "4: профили"]
EXAMPLE = [0x00, 0x82, 0x00, 0x00]

if __name__ == "__main__":
  out = figures_dir() / "ch07-emv" / "csu-anatomy.svg"
  write_svg(out, bitgrid(ROWS, LABELS, DEFINED, EXAMPLE))
