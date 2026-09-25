"""Генератор sbp-c2c-flow.svg для гл. 18 (СБП, сценарий C2C Push).

Порядок шагов -- по~тексту раздела C2C гл.~18 и~sbp-faq-transfers:
банк по~умолчанию, выбор банка отправителем, запрос готовности банка
получателя, расчёт в~ПС БР, зачисление.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import figures_dir, write_svg
from _seq import Act, Msg, Party, sequence

PARTIES = [
  Party("snd", "Отправитель", "мобильный банк"),
  Party("sbank", "Банк отправителя", "исходящий перевод", side="AccentA"),
  Party("opkc", "ОПКЦ СБП", "НСПК, ПС БР"),
  Party("rbank", "Банк получателя", "приём и зачисление", side="AccentB"),
]

EVENTS = [
  Msg("snd", "sbank", "номер телефона"),
  Msg("sbank", "opkc", "запрос: банк по умолчанию?"),
  Msg("opkc", "sbank", "банк по умолчанию (если задан)", reply=True),
  Msg("snd", "sbank", "выбор банка получателя", strong=True,
      note="банк выбирает отправитель"),
  Msg("sbank", "opkc", "поручение на перевод"),
  Msg("opkc", "rbank", "готов принять перевод?"),
  Msg("rbank", "opkc", "готов", reply=True),
  Act("opkc", "расчёт ПС БР"),
  Msg("opkc", "rbank", "зачисление средств", tone="Good", strong=True),
]

if __name__ == "__main__":
  out = figures_dir() / "ch18-sbp" / "sbp-c2c-flow.svg"
  write_svg(out, sequence(PARTIES, EVENTS))
