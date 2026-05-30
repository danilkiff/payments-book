from dataclasses import dataclass, field


@dataclass(frozen=True)
class Leg:
  debit: str
  credit: str
  amount: int  # в минорных единицах (копейках)

  def __post_init__(self) -> None:
    if self.amount <= 0:
      raise ValueError("сумма проводки должна быть положительной")


@dataclass
class Ledger:
  journal: list[Leg] = field(default_factory=list)

  def post(self, *legs: Leg) -> None:
    self.journal.extend(legs)

  def balance(self, account: str) -> int:
    total = 0
    for leg in self.journal:
      if leg.credit == account:
        total += leg.amount
      elif leg.debit == account:
        total -= leg.amount
    return total


# Применение событий этой главы: одна функция -- одна группа проводок.


def authorize(ledger: Ledger, amount: int) -> None:
  ledger.post(Leg("cardholder_receivable", "merchant_pending", amount))


def confirm(ledger: Ledger, amount: int, fee: int) -> None:
  ledger.post(
    Leg("merchant_pending", "merchant_earned", amount - fee),
    Leg("merchant_pending", "platform_fee_earned", fee),
  )


def settle(ledger: Ledger, amount: int) -> None:
  ledger.post(Leg("merchant_earned", "merchant_available", amount))


def refund(ledger: Ledger, amount: int) -> None:
  ledger.post(Leg("merchant_available", "refund_payable", amount))
