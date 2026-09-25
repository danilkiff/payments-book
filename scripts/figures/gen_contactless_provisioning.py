"""Генератор contactless-provisioning.svg для гл. 8 (выпуск DPAN в кошелёк).

Порядок шагов -- по~подразделу гл.~8 о~выпуске DPAN и~источникам
apple-card-provisioning-security, google-pay-device-tokenization-overview.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import figures_dir, write_svg
from _seq import Act, Msg, Party, sequence


PARTIES = [
  Party("holder", "Держатель", ""),
  Party("wallet", "Кошелёк (SE/HCE)", ""),
  Party("tsp", "TSP (сеть)", "хранилище токенов\n(внутри TSP)"),
  Party("issuer", "Эмитент", ""),
]

EVENTS = [
  Msg("holder", "wallet", "PAN"),
  Msg("wallet", "tsp", "PAN + данные устройства", note="+ Token Requestor ID"),
  Msg("tsp", "issuer", "запрос ID&V"),
  Msg("issuer", "tsp", "ID&V → решение эмитента", tone="Good", note="одобрено"),
  Msg("issuer", "tsp", "условно (доп. проверка)", tone="Warn", reply=True),
  Msg("issuer", "tsp", "отказ", tone="Bad"),
  Msg("tsp", "wallet", "DPAN + ключи", strong=True),
  Act("wallet", "SE"),
  Act("wallet", "HCE"),
  Msg("wallet", "holder", "«Карта добавлена»"),
]


if __name__ == "__main__":
  out = figures_dir() / "ch08-contactless" / "contactless-provisioning.svg"
  write_svg(out, sequence(PARTIES, EVENTS))
