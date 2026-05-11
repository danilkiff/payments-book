"""Verification for the ledger postings shown in ch33."""

import re

import pytest

from posting import (
  BANK_ACCOUNT_MAPPING,
  Ledger,
  Leg,
  authorize,
  confirm,
  refund,
  settle,
)


def test_canonical_marketplace_flow_balances():
  """Сквозной пример из ch33: 5000 руб., комиссия 10%, частичный возврат 2000."""
  ledger = Ledger()
  authorize(ledger, 5_000_00)
  confirm(ledger, 5_000_00, fee=500_00)
  settle(ledger, 4_500_00)
  refund(ledger, 2_000_00)

  # Активный счёт: требование к покупателю на исходную сумму. Знак
  # отрицательный по convention РСБУ -- активы накапливают дебет.
  assert ledger.balance("cardholder_receivable") == -5_000_00
  # Транзитные обязательства закрыты после подтверждения и расчёта.
  assert ledger.balance("merchant_pending") == 0
  assert ledger.balance("merchant_earned") == 0
  # Пассивные счета: платформа должна продавцу 2500 руб. после возврата,
  # признала 500 руб. комиссии, должна покупателю 2000 руб. возврата.
  assert ledger.balance("merchant_available") == 2_500_00
  assert ledger.balance("platform_fee_earned") == 500_00
  assert ledger.balance("refund_payable") == 2_000_00


def test_double_entry_keeps_total_balance_zero_at_every_step():
  """Сумма сальдо по всем затронутым счетам должна оставаться нулём."""
  ledger = Ledger()
  steps = (
    lambda: authorize(ledger, 5_000_00),
    lambda: confirm(ledger, 5_000_00, fee=500_00),
    lambda: settle(ledger, 4_500_00),
    lambda: refund(ledger, 2_000_00),
  )
  for step in steps:
    step()
    accounts = {leg.debit for leg in ledger.journal} | {
      leg.credit for leg in ledger.journal
    }
    assert sum(ledger.balance(a) for a in accounts) == 0


def test_balance_of_untouched_account_is_zero():
  ledger = Ledger()
  authorize(ledger, 1_000_00)
  assert ledger.balance("nonexistent") == 0


def test_post_rejects_non_positive_amounts():
  ledger = Ledger()
  with pytest.raises(ValueError, match="положительной"):
    ledger.post(Leg("a", "b", 0))
  with pytest.raises(ValueError, match="положительной"):
    ledger.post(Leg("a", "b", -100))


def test_full_refund_zeros_merchant_available():
  ledger = Ledger()
  authorize(ledger, 5_000_00)
  confirm(ledger, 5_000_00, fee=500_00)
  settle(ledger, 4_500_00)
  refund(ledger, 4_500_00)
  assert ledger.balance("merchant_available") == 0
  assert ledger.balance("refund_payable") == 4_500_00


def test_every_internal_account_has_809p_mapping():
  """Каждый внутренний счёт, появившийся в проводках, должен иметь маппинг."""
  ledger = Ledger()
  authorize(ledger, 5_000_00)
  confirm(ledger, 5_000_00, fee=500_00)
  settle(ledger, 4_500_00)
  refund(ledger, 2_000_00)
  used = {leg.debit for leg in ledger.journal} | {leg.credit for leg in ledger.journal}
  missing = used - BANK_ACCOUNT_MAPPING.keys()
  assert not missing, f"нет 809-П-соответствия для: {missing}"


def test_mapping_values_match_prefix_format():
  """Префикс: 5 цифр главы + дефис + 3 цифры валюты, либо None.

  В real-world АБС лицевой счёт 20-значный (плюс контрольный разряд,
  код подразделения, порядковый номер). Здесь показан только префикс,
  по которому однозначно определяются глава 809-П и валюта.

  None допускается явно: часть продуктовых состояний (например,
  авторизационный pending) на 809-П вовсе не отражается.
  """
  pattern = re.compile(r"^\d{5}-\d{3}$")
  for name, account in BANK_ACCOUNT_MAPPING.items():
    if account is None:
      continue
    assert pattern.match(account), f"{name}: {account!r} не соответствует формату"


def test_pending_state_is_explicitly_off_balance():
  """merchant_pending не имеет 809-П-соответствия: авторизация -- не движение."""
  assert BANK_ACCOUNT_MAPPING["merchant_pending"] is None
