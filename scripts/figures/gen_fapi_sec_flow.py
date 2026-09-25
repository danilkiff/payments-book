"""Генератор fapi-sec-flow.svg для гл. 20 (ФАПИ.СЕК, инициация платежа).

Шаги -- по~тексту гл.~20 и~fapi-sec-2024: PAR с~подписанным request object,
SCA и~согласие в~банке, обмен кода на~access_token, вызов API инициации,
расчёт через ОПКЦ СБП.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import figures_dir, write_svg
from _seq import Msg, Party, Phase, sequence

PARTIES = [
  Party("psu", "Клиент"),
  Party("tpp", "TPP / СПУ", "клиентское ПО", side="AccentB"),
  Party("aspsp", "ASPSP / ПУ", "банк счёта", side="AccentA"),
  Party("opkc", "ОПКЦ СБП", "расчёт"),
]

EVENTS = [
  Phase("Авторизация плательщика (ФАПИ.СЕК)"),
  Msg("psu", "tpp", "запуск оплаты"),
  Msg("tpp", "aspsp", "PAR: подписанный request object", strong=True,
      note="ответ: request_uri"),
  Msg("tpp", "psu", "редирект клиента → ASPSP"),
  Msg("psu", "aspsp", "аутентификация (SCA) + согласие", tone="Good",
      strong=True, note="банк проверяет подпись request object"),
  Msg("aspsp", "tpp", "authorization_code (callback)"),
  Msg("tpp", "aspsp", "token endpoint: code → access_token", strong=True,
      note="токен привязан к mTLS / DPoP"),
  Msg("tpp", "aspsp", "API инициации платежа (access_token)", strong=True),
  Phase("Расчёт и подтверждение"),
  Msg("aspsp", "opkc", "расчёт через СБП", tone="Good"),
  Msg("opkc", "psu", "финальный статус — асинхронно (webhook / polling)",
      reply=True),
]

if __name__ == "__main__":
  out = figures_dir() / "ch20-open-banking" / "fapi-sec-flow.svg"
  write_svg(out, sequence(PARTIES, EVENTS))
