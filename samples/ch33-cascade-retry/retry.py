from dataclasses import dataclass
from enum import Enum


class Decision(Enum):
  RETRY_SAME = "retry"
  CASCADE = "cascade"
  FAIL = "fail"


# Каноничные имена DE 39 по ISO 8583:1987; по 2 на класс для иллюстрации.

# Реквизиты карты или статус -- повтор и каскад не помогут.
INVALID_CARD_NUMBER = "14"
EXPIRED_CARD = "54"
HARD_DECLINES = frozenset({INVALID_CARD_NUMBER, EXPIRED_CARD})

# Сбой канала или эмитента -- безопасно повторить тому же эквайеру.
ISSUER_INOPERATIVE = "91"
SYSTEM_MALFUNCTION = "96"
TRANSIENT = frozenset({ISSUER_INOPERATIVE, SYSTEM_MALFUNCTION})

# Иной маршрут (BIN эквайера, MCC, Terminal ID) может дать иной ответ.
DO_NOT_HONOR = "05"
INSUFFICIENT_FUNDS = "51"
SOFT_DECLINES = frozenset({DO_NOT_HONOR, INSUFFICIENT_FUNDS})


@dataclass(frozen=True)
class Attempt:
  acquirer: str
  response_code: str


def decide(
  history: list[Attempt],
  available_acquirers: list[str],
  max_retries: int = 1,
  max_cascade: int = 2,
) -> Decision:
  if not history:
    raise ValueError("history пуст: первая попытка делается без решения")

  last = history[-1]
  code = last.response_code

  if code in HARD_DECLINES:
    return Decision.FAIL

  if code in TRANSIENT:
    same = sum(1 for a in history if a.acquirer == last.acquirer)
    if same <= max_retries:
      return Decision.RETRY_SAME
    return Decision.FAIL

  if code in SOFT_DECLINES:
    tried = {a.acquirer for a in history}
    remaining = set(available_acquirers) - tried
    if remaining and len(tried) <= max_cascade:
      return Decision.CASCADE
    return Decision.FAIL

  # Незнакомый код -- безопаснее не повторять.
  return Decision.FAIL
