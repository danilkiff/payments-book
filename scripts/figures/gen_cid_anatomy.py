"""Генератор cid-anatomy.svg для гл. 7 EMV (GENERATE AC: запрос и ответ).

P1 команды GENERATE AC задаёт, какую криптограмму терминал запрашивает
(биты 8--7: тип; бит 6: запросить CDA). CID (Cryptogram Information Data,
тег 9F27) в ответе сообщает фактически выданный тип (биты 8--7), признак
advice (бит 4) и код причины (биты 3--1).
Пример: P1 = 0xA0 (запрос ARQC + CDA), CID = 0x80 (карта вернула ARQC).
Источник: emvco-book3, §6.5.5 и Table 14.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bitgrid import bitgrid
from _common import figures_dir, write_svg

LABELS = {
  (0, 8): "тип", (0, 6): "CDA",
  (1, 8): "тип", (1, 4): "advice", (1, 3): "причина",
}
DEFINED = {
  (0, 8), (0, 7), (0, 6),
  (1, 8), (1, 7), (1, 4), (1, 3), (1, 2), (1, 1),
}
ROWS = ["P1: запрос", "CID 9F27: ответ"]
EXAMPLE = [0xA0, 0x80]
NOTES = ["запрос ARQC + CDA", "карта вернула ARQC"]

if __name__ == "__main__":
  out = figures_dir() / "ch07-emv" / "cid-anatomy.svg"
  write_svg(out, bitgrid(ROWS, LABELS, DEFINED, EXAMPLE, NOTES))
