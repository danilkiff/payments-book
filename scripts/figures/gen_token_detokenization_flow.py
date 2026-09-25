"""Генератор token-detokenization-flow.svg для гл. 9 (токенизированная авторизация).

Шаги -- по~разделу гл.~9 о~детокенизации (emvco-payment-tokenisation):
BIN токена ведёт запрос в~TSP, TSP подменяет DPAN на~FPAN и~обратно.
Сторона AccentA видит только DPAN, сторона AccentB (эмитент) -- FPAN.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import figures_dir, write_svg
from _seq import Msg, Party, Phase, sequence


PARTIES = [
  Party("holder", "Держатель", "мобильный\nкошелёк", side="AccentA"),
  Party("tsp_m", "ТСП", "видит только\nDPAN", side="AccentA"),
  Party("acq", "Эквайер /\nPSP", "видит только\nDPAN", side="AccentA"),
  Party("net", "Карточная\nсеть", "DPAN <-> FPAN"),
  Party("vault", "TSP / Vault", "mapping +\nassurance"),
  Party("iss", "Эмитент", "видит FPAN\n+ meta", side="AccentB"),
]

EVENTS = [
  Phase("Запрос авторизации (request leg)"),
  Msg("holder", "tsp_m", "DPAN + TAVV", strong=True),
  Msg("tsp_m", "acq", "DPAN + сумма + MID + TRID", strong=True),
  Msg("acq", "net", "MTI 0100 · DE 2 = DPAN", strong=True,
      note="BIN из token range -> маршрут в TSP"),
  Msg("net", "vault", "detokenize", strong=True),
  Msg("vault", "net", "FPAN + Token Assurance", strong=True, reply=True),
  Msg("net", "iss", "MTI 0100 · DE 2 = FPAN · TAL", strong=True),
  Phase("Ответ авторизации (response leg)"),
  Msg("iss", "net", "MTI 0110 · DE 2 = FPAN · DE 39 = 00", strong=True,
      tone="Good", reply=True),
  Msg("net", "holder", "MTI 0110 · DE 2 = DPAN — продавцу и держателю",
      strong=True, tone="Good", reply=True),
]

if __name__ == "__main__":
  out = figures_dir() / "ch09-tokenization" / "token-detokenization-flow.svg"
  write_svg(out, sequence(PARTIES, EVENTS))
