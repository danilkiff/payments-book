"""Генератор pisp-flow.svg для гл. 20 (Open Banking UK, поток PISP).

Одиночный платёж внутри страны, две фазы жизненного цикла
payment-consent -- по~openbanking-uk-payment-initiation-profile и~psd2.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import figures_dir, write_svg
from _seq import Msg, Party, Phase, sequence

PARTIES = [
  Party("psu", "Клиент"),
  Party("pisp", "ТСП / PISP", "TPP", side="AccentB"),
  Party("aspsp", "ASPSP", "банк плательщика", side="AccentA"),
]

EVENTS = [
  Phase("Создание согласия на платёж с SCA (PSD2 Art. 97)"),
  Msg("psu", "pisp", "выбор PISP-оплаты"),
  Msg("pisp", "aspsp", "POST /domestic-payment-consents", strong=True,
      note="client_credentials → ConsentId"),
  Msg("pisp", "psu", "redirect → ASPSP"),
  Msg("psu", "aspsp", "SCA: два фактора", tone="Good", strong=True,
      note="consent → Authorised"),
  Msg("aspsp", "pisp", "authorization_code"),
  Msg("pisp", "aspsp", "POST /token", strong=True, note="code → access_token"),
  Phase("Инициация платежа: POST /domestic-payments и опрос статуса"),
  Msg("pisp", "aspsp", "POST /domestic-payments", strong=True,
      note="access_token → PaymentId"),
  Msg("aspsp", "pisp", "опрос статуса (асинхронно)", reply=True,
      note="Pending → AcceptedSettlementCompleted / Rejected"),
  Msg("pisp", "psu", "подтверждение заказа", tone="Good"),
]

if __name__ == "__main__":
  out = figures_dir() / "ch20-open-banking" / "pisp-flow.svg"
  write_svg(out, sequence(PARTIES, EVENTS))
