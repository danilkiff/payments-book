"""Генератор sbp-c2b-flow.svg для гл. 18 (СБП, сценарий C2B).

Порядок шагов -- по~тексту раздела C2B гл.~18: cbr-ps, cbr-sbp-actions,
sbp-faq-business, sbpay-app.
Пять участников не~помещаются в~равные полосы: ширина полосы по~участнику.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import figures_dir, write_svg
from _seq import Act, Msg, Party, Phase, sequence


PARTIES = [
  Party("buyer", "Покупатель", "мобильный банк, СБПэй"),
  Party("seller", "Продавец", "сайт, касса, QR"),
  Party("pbank", "Банк плательщика", "списание со счёта", side="AccentA"),
  Party("opkc", "ОПКЦ СБП", "НСПК, ПС БР"),
  Party("rbank", "Банк получателя", "зачисление на счёт", side="AccentB"),
]
LANES = [95, 64, 86, 56, 79]

EVENTS = [
  Msg("seller", "buyer", "QR / кнопка / ссылка"),
  Msg("buyer", "pbank", "подтверждение списания", strong=True),
  Msg("pbank", "opkc", "операция перевода"),
  Act("opkc", "маршрутизация ОПКЦ"),
  Act("opkc", "расчёт ПС БР"),
  Msg("opkc", "rbank", "зачисление средств", tone="Good", strong=True),
  Phase("точка финальности"),
  Msg("rbank", "seller", "финальный статус операции", tone="Good"),
  Msg("seller", "buyer", "подтверждение заказа / товар", tone="Good"),
]

if __name__ == "__main__":
  out = figures_dir() / "ch18-sbp" / "sbp-c2b-flow.svg"
  write_svg(out, sequence(PARTIES, EVENTS, lanes=LANES))
