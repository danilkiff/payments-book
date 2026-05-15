from dataclasses import dataclass
from enum import Enum

HOUR = 3600
DAY = 24 * HOUR


class Action(Enum):
  RETRY = "retry"  # повтор разрешён, ждать wait_seconds
  STOP = "stop"  # запрет повторов по этим реквизитам
  REFRESH = "refresh"  # реквизиты устарели, получить новые (ABU/VAU)


# Merchant Advice Code -- проприетарный код Mastercard, передаётся в DE 48
# (Additional Data -- Private Use) авторизационного ответа.
# 03 -- Do not try again; 01 -- New account information available;
# 24-30 -- временный отказ, повтор после ожидания.
MAC_DO_NOT_TRY_AGAIN = "03"
MAC_NEW_ACCOUNT_INFO = "01"

WAIT_BY_MAC: dict[str, int] = {
  "24": 1 * HOUR,
  "25": 1 * DAY,
  "26": 2 * DAY,
  "27": 4 * DAY,
  "28": 6 * DAY,
  "29": 8 * DAY,
  "30": 10 * DAY,
}


@dataclass(frozen=True)
class Decision:
  action: Action
  wait_seconds: int = 0  # имеет смысл только для Action.RETRY


def classify(mac: str) -> Decision:
  if mac == MAC_DO_NOT_TRY_AGAIN:
    return Decision(Action.STOP)
  if mac == MAC_NEW_ACCOUNT_INFO:
    return Decision(Action.REFRESH)
  wait = WAIT_BY_MAC.get(mac)
  if wait is not None:
    return Decision(Action.RETRY, wait_seconds=wait)
  # Неизвестный MAC -- безопасный вариант: не повторять автоматически.
  return Decision(Action.STOP)
