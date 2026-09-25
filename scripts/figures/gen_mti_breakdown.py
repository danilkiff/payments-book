"""Генератор mti-breakdown.svg для гл. 6 ISO 8583, раздел "MTI и стадия транзакции".

Четыре позиции MTI (версия, класс, функция, инициатор) со~значениями
по~fis-iso8583-guide-2023; выделены цифры примера MTI 0100.
Раскладка -- positions_svg() из~gen_service_code.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import figures_dir, write_svg
from gen_service_code import positions_svg

POSITIONS = [
  ("Позиция 1", "", [
    ("0", "ISO 8583:1987"),
    ("1", "ред. 1993"),
    ("2", "ред. 2003"),
    ("3", "ред. 2023"),
  ], "0"),
  ("Позиция 2", "", [
    ("1", "авторизация"),
    ("2", "финансовое"),
    ("3", "file action"),
    ("4", "reversal, chargeback"),
    ("5", "reconciliation"),
    ("6", "административное"),
    ("7", "fee collection"),
    ("8", "управление сетью"),
  ], "1"),
  ("Позиция 3", "", [
    ("0", "request"),
    ("1", "request response"),
    ("2", "advice"),
    ("3", "advice response"),
    ("4", "notification"),
    ("5", "notification ack"),
    ("6", "instruction"),
    ("7", "instruction ack"),
  ], "0"),
  ("Позиция 4", "", [
    ("0", "эквайер"),
    ("1", "эквайер, повтор"),
    ("2", "эмитент"),
    ("3", "эмитент, повтор"),
    ("4", "др. сторона"),
    ("5", "др. сторона, повтор"),
  ], "0"),
]

if __name__ == "__main__":
  write_svg(figures_dir() / "ch06-iso8583" / "mti-breakdown.svg",
            positions_svg(POSITIONS, gap=4))
