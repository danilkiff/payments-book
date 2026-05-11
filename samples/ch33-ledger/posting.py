"""Минимальный реестр обязательств на двойной записи.

Каждая проводка (Leg) -- атомарная пара "дебет счёта A, кредит счёта B
на одну и ту же сумму". Событие платёжного потока порождает группу
проводок; инвариант "сумма дебетов = сумма кредитов" выполняется
по построению каждой Leg.
"""

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
