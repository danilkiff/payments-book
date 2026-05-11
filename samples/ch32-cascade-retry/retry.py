from dataclasses import dataclass
from enum import Enum


class Decision(Enum):
  RETRY_SAME = "retry"
  CASCADE = "cascade"
  FAIL = "fail"


# Реквизиты карты или статус -- повтор и каскад не помогут.
HARD_DECLINES = frozenset(
  {
    "04",  # изъятие карты
    "07",  # изъятие карты, особое условие
    "12",  # невалидная транзакция
    "14",  # несуществующий номер карты
    "41",  # карта заявлена утерянной
    "43",  # карта заявлена украденной
    "54",  # карта просрочена
    "57",  # операция не разрешена держателю
    "58",  # операция не разрешена терминалу
  }
)

# Сбой канала или эмитента -- безопасно повторить тому же эквайеру.
TRANSIENT = frozenset(
  {
    "19",  # re-enter transaction (таймаут / нет ответа)
    "91",  # эмитент или коммутатор недоступен
    "96",  # сбой системы
  }
)

# Иной маршрут (BIN эквайера, MCC, Terminal ID) может дать иной ответ.
SOFT_DECLINES = frozenset(
  {
    "05",  # do not honor (отказ без объяснения)
    "51",  # недостаточно средств
    "61",  # превышен лимит суммы
    "62",  # карта с ограничениями
    "65",  # превышен лимит частоты
  }
)


@dataclass(frozen=True)
class Attempt:
  acquirer: str
  response_code: str


def decide(
  history: list[Attempt],
  available_acquirers: list[str],
  *,
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
    if not set(available_acquirers) - tried:
      return Decision.FAIL
    if len(tried) >= max_cascade + 1:
      return Decision.FAIL
    return Decision.CASCADE

  # Незнакомый код -- безопаснее не повторять.
  return Decision.FAIL
