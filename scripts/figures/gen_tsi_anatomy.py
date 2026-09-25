"""Генератор tsi-anatomy.svg для гл. 7 EMV.

TSI -- тег 0x9B, 2 байта битовых флагов выполненных функций в~EMV-
транзакции (counterpart TVR: TVR пишет провалы/факты проверок, TSI
пишет "что было выполнено").

Байт 1: ODA, CV, Card RM, Issuer auth, Terminal RM, Script processing.
Байт 2: весь RFU.

Пример: TSI = 0xE800 -- офлайн-транзакция, всё выполнено кроме online-этапов.
Источник: emvco-book3 Annex C7.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bitgrid import bitgrid
from _common import figures_dir, write_svg

LABELS = {
  (0, 8): "ODA",
  (0, 7): "CV",
  (0, 6): "Card RM",
  (0, 5): "Issuer auth",
  (0, 4): "Term RM",
  (0, 3): "Script",
  **{(1, b): "RFU" for b in range(1, 9)},
}
DEFINED = {(0, 8), (0, 7), (0, 6), (0, 5), (0, 4), (0, 3)}
ROWS = ["Байт 1", "Байт 2"]
EXAMPLE = [0xE8, 0x00]

if __name__ == "__main__":
  out = figures_dir() / "ch07-emv" / "tsi-anatomy.svg"
  write_svg(out, bitgrid(ROWS, LABELS, DEFINED, EXAMPLE))
