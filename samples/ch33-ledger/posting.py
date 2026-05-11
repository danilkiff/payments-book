from dataclasses import dataclass, field


@dataclass(frozen=True)
class Leg:
  debit: str
  credit: str
  amount: int  # в минорных единицах (копейках)


@dataclass
class Ledger:
  journal: list[Leg] = field(default_factory=list)

  def post(self, *legs: Leg) -> None:
    for leg in legs:
      if leg.amount <= 0:
        raise ValueError("сумма проводки должна быть положительной")
    self.journal.extend(legs)

  def balance(self, account: str) -> int:
    """Сальдо счёта: сумма кредитов минус сумма дебетов.

    Convention РСБУ-учёта (как в АБС вроде RS-Bank): активные счета
    (receivable, available) показывают отрицательный остаток,
    пассивные (payable, earned, pending) -- положительный.
    """
    return sum(
      -leg.amount if leg.debit == account else leg.amount
      for leg in self.journal
      if account in (leg.debit, leg.credit)
    )


# Применение событий из ch33: одна функция -- одна группа проводок.


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


# Иллюстративное соответствие внутренних счетов продуктового реестра
# и счетов 809-П на стороне банка-эквайера (либо банка-партнёра
# небанковского продукта). В production маппинг утверждается учётной
# политикой и зависит от схемы расчётов.
#
# Формат: <глава, 5 знаков>-<код валюты, 3 знака; 810 -- рубль
# во внутренней нотации балансовых счетов банка>.
BANK_ACCOUNT_MAPPING: dict[str, str] = {
  "cardholder_receivable": "30233-810",  # активный: незавершённые расчёты по картам
  "merchant_pending": "47422-810",  # пассивный: обязательства по прочим операциям
  "merchant_earned": "47422-810",  # тот же счёт; продукт сам ведёт аналитический срез
  "merchant_available": "47422-810",
  "platform_fee_earned": "70601-810",  # пассивный: операционные доходы (комиссии)
  "refund_payable": "47422-810",
}
