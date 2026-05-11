"""Решение о следующей попытке после отказа эквайера.

Чистая функция, без побочных эффектов и без обращения к сети. Различает
три класса ответов:

* hard decline -- больше попыток не делать (реквизиты неверны,
  карта в стоп-листе);
* transient -- повторить запрос тому же эквайеру (сбой инфраструктуры);
* soft decline -- каскадировать другому эквайеру (иной маршрут может
  дать иной ответ того же эмитента).

Списки кодов иллюстративны: в production-системе они задаются правилами
схемы и спецификацией процессинга. См. ch32 \"Каскадная маршрутизация\".
"""

from dataclasses import dataclass
from enum import Enum


class Decision(Enum):
    RETRY_SAME = "retry"
    CASCADE = "cascade"
    FAIL = "fail"


# Реквизиты карты или статус -- повтор и каскад не помогут.
HARD_DECLINES = frozenset({"04", "07", "12", "14", "41", "43", "54", "57", "58"})

# Сбой канала или эмитента -- безопасно повторить тому же эквайеру.
TRANSIENT = frozenset({"19", "91", "96"})

# Иной маршрут (BIN эквайера, MCC, Terminal ID) может дать иной ответ.
SOFT_DECLINES = frozenset({"05", "51", "61", "62", "65"})


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
