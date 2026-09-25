"""Генератор bnpl-psp-purchase.svg для гл. 22 (BNPL, покупка через провайдера).

Порядок шагов -- по~тексту раздела о~модели PSP гл.~22,
klarna-settlement-reports и~tbank-dolyame-api.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import figures_dir, write_svg
from _seq import Act, Msg, Party, sequence

PARTIES = [
  Party("cli", "Клиент", side="AccentA"),
  Party("tsp", "ТСП"),
  Party("bnpl", "BNPL-провайдер", side="AccentB"),
]

EVENTS = [
  Msg("cli", "tsp", "оформление заказа, выбор BNPL"),
  Msg("tsp", "bnpl", "SDK / API: orderId, сумма"),
  Msg("bnpl", "cli", "график: 4 платежа × 25 % (Pay-in-4)"),
  Msg("cli", "bnpl", "подтверждение + сохранение credential",
      note="CIT · stored credential"),
  Act("bnpl", "скоринг"),
  Msg("bnpl", "tsp", "webhook: approved"),
  Msg("bnpl", "tsp", "settlement (−комиссия)", reply=True, strong=True),
  Msg("tsp", "cli", "товар отгружен"),
]

if __name__ == "__main__":
  out = figures_dir() / "ch22-bnpl" / "bnpl-psp-purchase.svg"
  write_svg(out, sequence(PARTIES, EVENTS))
