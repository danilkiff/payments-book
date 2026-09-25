"""Генератор sbp-me2me-pull-flow.svg для гл. 18 (СБП, сценарий Me2Me Pull).

Порядок шагов -- по~тексту раздела C2C гл.~18 и~sbp-faq-settings:
стягивание инициирует банк-получатель, согласие на~списание клиент даёт
в~банке-отправителе по~ссылке из~уведомления.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import figures_dir, write_svg
from _seq import Act, Msg, Party, sequence

PARTIES = [
  Party("client", "Клиент", "одно согласие"),
  Party("rbank", "Банк-получатель", "инициатор стягивания", side="AccentB"),
  Party("opkc", "ОПКЦ СБП", "маршрутизация НСПК · ПС БР"),
  Party("sbank", "Банк-отправитель", "счёт списания · согласие", side="AccentA"),
]
LANES = [70, 92, 116, 100]

EVENTS = [
  Msg("client", "rbank", "запускает стягивание"),
  Msg("rbank", "opkc", "запрос на стягивание"),
  Msg("opkc", "sbank", "запрос списания"),
  Msg("sbank", "client", "уведомление со ссылкой", reply=True, tone="Warn",
      strong=True),
  Msg("client", "sbank", "согласие на списание (разовое / постоянное)",
      tone="Warn", strong=True, note="даётся в банке-отправителе"),
  Msg("sbank", "opkc", "средства списаны", tone="Good"),
  Act("opkc", "расчёт ПС БР"),
  Msg("opkc", "rbank", "зачисление на счёт", tone="Good", strong=True),
]

if __name__ == "__main__":
  out = figures_dir() / "ch18-sbp" / "sbp-me2me-pull-flow.svg"
  write_svg(out, sequence(PARTIES, EVENTS, lanes=LANES))
