import pytest

from mac import DAY, HOUR, Action, classify

# MAC 24-30: ожидание перед повтором, секунды.
RETRY_WAITS = [
  ("24", 1 * HOUR),
  ("25", 1 * DAY),
  ("26", 2 * DAY),
  ("27", 4 * DAY),
  ("28", 6 * DAY),
  ("29", 8 * DAY),
  ("30", 10 * DAY),
]


def test_mac_03_stops_retries():
  assert classify("03").action is Action.STOP


def test_mac_01_requests_refresh():
  assert classify("01").action is Action.REFRESH


@pytest.mark.parametrize("mac, expected_wait", RETRY_WAITS)
def test_retry_mac_returns_wait_per_table(mac, expected_wait):
  d = classify(mac)
  assert d.action is Action.RETRY
  assert d.wait_seconds == expected_wait


def test_retry_waits_are_strictly_monotonic():
  # Контракт схемы: каждая следующая retry-категория откладывает повтор дальше.
  waits = [w for _, w in RETRY_WAITS]
  assert waits == sorted(waits)
  assert len(set(waits)) == len(waits)


@pytest.mark.parametrize("mac", ["", "99"])
def test_unknown_mac_defaults_to_stop(mac):
  assert classify(mac).action is Action.STOP


@pytest.mark.parametrize("mac", ["02", "04", "10", "20"])
def test_known_non_retry_mac_stops(mac):
  # Коды вне 24-30 / 01 / 03: классификатор обязан вернуть STOP,
  # а не RETRY с нулевым ожиданием.
  assert classify(mac).action is Action.STOP
