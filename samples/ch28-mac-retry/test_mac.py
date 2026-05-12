from mac import DAY, HOUR, Action, classify


def test_mac_03_stops_retries():
  d = classify("03")
  assert d.action is Action.STOP


def test_mac_01_requests_refresh():
  d = classify("01")
  assert d.action is Action.REFRESH


def test_mac_24_returns_one_hour_wait():
  d = classify("24")
  assert d.action is Action.RETRY
  assert d.wait_seconds == 1 * HOUR


def test_mac_25_returns_one_day_wait():
  d = classify("25")
  assert d.action is Action.RETRY
  assert d.wait_seconds == 1 * DAY


def test_mac_30_returns_ten_days_wait():
  d = classify("30")
  assert d.action is Action.RETRY
  assert d.wait_seconds == 10 * DAY


def test_wait_grows_monotonically_across_mac_24_to_30():
  waits = [classify(str(code)).wait_seconds for code in range(24, 31)]
  assert waits == sorted(waits)
  # И ни одно значение не повторяется.
  assert len(set(waits)) == len(waits)


def test_unknown_mac_defaults_to_stop():
  # Незнакомый код -- не повторять. Так схема не штрафует за лишний цикл.
  assert classify("99").action is Action.STOP
  assert classify("").action is Action.STOP


def test_known_mac_codes_not_in_24_30_range():
  # MAC 02, 04-10 в публичных правилах не описаны как retry-категория;
  # классификатор обязан их трактовать как STOP, а не как нулевое ожидание.
  for code in ("02", "04", "10", "20"):
    assert classify(code).action is Action.STOP
