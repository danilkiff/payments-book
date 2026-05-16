"""Минимальный AML-классификатор для параграфа 1 главы ch26-aml.

Сопоставляет операцию с критериями обязательного контроля
(статья 6 115-ФЗ) и решает, в какой поток её отправить: обязательный
контроль, подозрительная операция (статья 7) или обычный поток.

Иллюстрация одной из шести программ ПВК по 860-П, программы
выявления операций. Перечень категорий сокращён, журнал аудита
и интеграция с программой управления риском сведены к полю reason,
которое отдаётся в Verdict для записи в журнал.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

# Пороги обязательного контроля по статье 6 115-ФЗ на 2026 г. (в копейках).
# Суммы хранятся в копейках, чтобы не вести арифметику с float.
GENERIC_THRESHOLD = 1_000_000_00
REAL_ESTATE_THRESHOLD = 5_000_000_00
GOV_ORDER_THRESHOLD = 600_000_00
POSTAL_THRESHOLD = 100_000_00


class Kind(StrEnum):
  CASH_DEPOSIT = "cash_deposit"  # внесение/снятие наличных, юрлицо
  CASH_FX = "cash_fx"  # покупка наличной валюты физлицом
  REAL_ESTATE = "real_estate"  # сделка с недвижимостью
  GOV_ORDER = "gov_order"  # счёт по гособоронзаказу
  POSTAL = "postal"  # почтовый перевод
  WIRE_TRANSFER = "wire_transfer"  # обычный безналичный перевод


class Decision(StrEnum):
  MANDATORY = "mandatory"  # статья 6: обязательный контроль
  SUSPICIOUS = "suspicious"  # статья 7: подозрительная операция
  NORMAL = "normal"  # обычный поток без эскалации


RiskTier = Literal["low", "medium", "high"]

_KINDS_WITH_MANDATORY = frozenset(
  {
    Kind.CASH_DEPOSIT,
    Kind.CASH_FX,
    Kind.REAL_ESTATE,
    Kind.GOV_ORDER,
    Kind.POSTAL,
  }
)


@dataclass(frozen=True)
class Operation:
  amount_kopecks: int
  kind: Kind
  client_id: str
  counterparty_id: str | None
  client_risk: RiskTier


@dataclass(frozen=True)
class Verdict:
  decision: Decision
  reason: str  # стабильный код причины для журнала аудита


def _threshold(kind: Kind) -> int:
  if kind == Kind.REAL_ESTATE:
    return REAL_ESTATE_THRESHOLD
  if kind == Kind.GOV_ORDER:
    return GOV_ORDER_THRESHOLD
  if kind == Kind.POSTAL:
    return POSTAL_THRESHOLD
  return GENERIC_THRESHOLD


def classify(op: Operation, sanctioned: frozenset[str]) -> Verdict:
  # Сторона из перечня экстремистов/террористов: обязательный контроль
  # независимо от суммы (статья 6 пункт 1.1, абзац о перечне).
  party_in_list = op.client_id in sanctioned or (
    op.counterparty_id is not None and op.counterparty_id in sanctioned
  )
  if party_in_list:
    return Verdict(Decision.MANDATORY, "party_in_list")

  threshold = _threshold(op.kind)

  # Сумма + категория операции: обязательный контроль по статье 6.
  if op.kind in _KINDS_WITH_MANDATORY and op.amount_kopecks >= threshold:
    return Verdict(Decision.MANDATORY, f"threshold:{op.kind.value}")

  # Risk-based approach: для высокорискового клиента нижняя граница
  # подозрительности сдвинута к половине формального порога. Конкретный
  # коэффициент задаёт программа управления риском в ПВК.
  if op.client_risk == "high" and op.amount_kopecks >= threshold // 2:
    return Verdict(Decision.SUSPICIOUS, "rba:high_risk_client")

  return Verdict(Decision.NORMAL, "below_threshold")
