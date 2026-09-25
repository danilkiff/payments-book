"""Генератор aip-anatomy.svg для гл. 7 EMV.

AIP -- тег 0x82, 2 байта битовых флагов возможностей карты:
- Байт 1: SDA, DDA, CDA, cardholder verification, terminal risk management,
  issuer authentication.
- Байт 2: в~основном RFU для EMV Contactless Specifications.

Пример: AIP = 0x5800 (SDA + CVM + TRM).
Источник: emvco-book3 (EMV Book 3 v4.4), open-source emv-tools (lumag/emv-tools).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bitgrid import bitgrid
from _common import figures_dir, write_svg

LABELS = {
  (0, 7): "SDA",
  (0, 6): "DDA",
  (0, 5): "CVM есть",
  (0, 4): "риск-мен.",
  (0, 3): "iss. auth",
  (0, 2): "RFU CL",
  (0, 1): "CDA",
  (1, 8): "RFU CL",
  (1, 7): "RFU CL",
  (1, 6): "RFU CL",
  (1, 1): "RFU CL",
}
DEFINED = {(0, 7), (0, 6), (0, 5), (0, 4), (0, 3), (0, 1)}
ROWS = ["Байт 1", "Байт 2"]
EXAMPLE = [0x58, 0x00]

if __name__ == "__main__":
  out = figures_dir() / "ch07-emv" / "aip-anatomy.svg"
  write_svg(out, bitgrid(ROWS, LABELS, DEFINED, EXAMPLE))
