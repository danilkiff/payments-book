"""Генератор 3ds-v1-flow.svg для гл. 11 (3-D Secure v1).

Порядок сообщений -- по~разделу 3DS v1 гл.~11: VEReq/VERes между MPI и~DS,
PAReq/PARes через браузер держателя карты; источник emvco-3ds-whitepaper.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import figures_dir, write_svg
from _seq import Msg, Party, sequence

PARTIES = [
  Party("hold", "Держатель"),
  Party("brw", "Браузер"),
  Party("mpi", "ТСП / MPI"),
  Party("ds", "DS"),
  Party("acs", "ACS"),
]

EVENTS = [
  Msg("hold", "mpi", "старт оплаты (через браузер)"),
  Msg("mpi", "ds", "VEReq"),
  Msg("ds", "mpi", "VERes", reply=True),
  Msg("mpi", "acs", "PAReq (через браузер)"),
  Msg("acs", "brw", "редирект / всплывающее окно"),
  Msg("hold", "brw", "пароль / OTP"),
  Msg("brw", "acs", "пароль / OTP (через браузер)"),
  Msg("acs", "mpi", "PARes", reply=True),
  Msg("mpi", "hold", "результат аутентификации", reply=True),
  Msg("mpi", "acs", "авторизация"),
]

if __name__ == "__main__":
  out = figures_dir() / "ch11-3ds" / "3ds-v1-flow.svg"
  write_svg(out, sequence(PARTIES, EVENTS))
