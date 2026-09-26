"""Генератор 3ds-v2-flow-frictionless.svg и~3ds-v2-flow-challenge.svg, гл. 11.

Поток EMV 3DS по~разделу 3DS v2 гл.~11, источник emvco-3ds-whitepaper.
Сценарии frictionless и~challenge разнесены по~двум фигурам: вместе они
выше CANVAS_H_MAX.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import figures_dir, write_svg
from _seq import Msg, Party, sequence

PARTIES = [
  Party("hold", "Держатель"),
  Party("req", "3DS Requestor"),
  Party("srv", "3DS Server"),
  Party("ds", "DS"),
  Party("acs", "ACS"),
]

FRICTIONLESS = [
  Msg("hold", "req", "старт оплаты"),
  Msg("hold", "acs", "3DS Method URL (скрытый iframe)"),
  Msg("req", "srv", "authReq"),
  Msg("srv", "ds", "AReq"),
  Msg("ds", "acs", "AReq"),
  Msg("acs", "srv", "ARes (transStatus=Y/N/A)", reply=True),
  Msg("srv", "req", "ARes", reply=True),
  Msg("req", "srv", "авторизация"),
]

CHALLENGE = [
  Msg("acs", "req", "ARes (transStatus=C, Challenge Required)", reply=True),
  Msg("hold", "acs", "CReq", note="UX: OTP / биометрия (вызов)"),
  Msg("acs", "hold", "CRes", reply=True),
  Msg("acs", "srv", "RReq"),
  Msg("srv", "acs", "RRes", reply=True),
  Msg("req", "srv", "авторизация"),
]

if __name__ == "__main__":
  d = figures_dir() / "ch11-3ds"
  write_svg(d / "3ds-v2-flow-frictionless.svg", sequence(PARTIES, FRICTIONLESS))
  write_svg(d / "3ds-v2-flow-challenge.svg", sequence(PARTIES, CHALLENGE))
