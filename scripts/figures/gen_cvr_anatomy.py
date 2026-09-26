"""Генератор cvr-anatomy.svg для гл. 7 EMV (CVR, результаты карты).

CVR (Card Verification Results) -- результаты проверок на~стороне карты,
зеркало TVR. Раскладка по~CCD Format A (EMV Book 3, Part V, Table CCD 10):
4 значащих байта внутри IAD (тег 9F10); пятый байт RFU и~не~показан.
Нибл-поля (тип AC, счётчик попыток PIN, число команд скрипта) шире 1~бита --
подписан левый бит поля, остальные ячейки поля затенены как определённые.
Жёлтым подсвечен пример CVR = 0xA8 38 00 00: 1-й GENERATE AC вернул ARQC,
2-й не~запрашивался, выполнена CDA, офлайн-PIN проверён, остаток попыток PIN = 3.
Источник: emvco-book3 + проза § CVR.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bitgrid import bitgrid
from _common import figures_dir, write_svg

# Левый бит нибл-поля несёт имя, остальные ячейки поля только затеняются.
LABELS = {
  (0, 8): "AC 2-й", (0, 6): "AC 1-й",
  (0, 4): "CDA", (0, 3): "DDA офл", (0, 2): "IA нет", (0, 1): "IA пров",
  (1, 8): "PTC",
  (1, 4): "офл PIN", (1, 3): "PIN✗", (1, 2): "PTL", (1, 1): "онл✗",
  (2, 8): "ниж N", (2, 7): "вер N", (2, 6): "ниж S", (2, 5): "вер S",
  (3, 8): "N сцен",
  (3, 4): "сцен✗", (3, 3): "ODA пр", (3, 2): "онл сл", (3, 1): "!онл",
}
DEFINED = {
  *((0, b) for b in range(1, 9)),
  *((1, b) for b in range(1, 9)),
  (2, 8), (2, 7), (2, 6), (2, 5),
  *((3, b) for b in range(1, 9)),
}
ROWS = ["1: AC + аутент.", "2: PIN", "3: лимиты", "4: сценарий"]
EXAMPLE = [0xA8, 0x38, 0x00, 0x00]

if __name__ == "__main__":
  out = figures_dir() / "ch07-emv" / "cvr-anatomy.svg"
  write_svg(out, bitgrid(ROWS, LABELS, DEFINED, EXAMPLE))
