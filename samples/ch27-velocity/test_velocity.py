"""Verification for the velocity rule shown in ch27."""

from velocity import VelocityRule


class FakeClock:
  """Управляемые часы: тесты не зависят от реального времени."""

  def __init__(self, start: float = 0.0) -> None:
    self.t = start

  def __call__(self) -> float:
    return self.t

  def advance(self, seconds: float) -> None:
    self.t += seconds


def test_under_threshold_all_events_pass():
  clock = FakeClock()
  rule = VelocityRule(window_sec=60, max_events=5, now=clock)
  for _ in range(5):
    assert rule.check("card_1") is True
    clock.advance(1)


def test_threshold_exceeded_returns_false():
  clock = FakeClock()
  rule = VelocityRule(window_sec=60, max_events=3, now=clock)
  assert rule.check("card_1") is True
  assert rule.check("card_1") is True
  assert rule.check("card_1") is True
  # Четвёртое событие в том же окне -- превышение.
  assert rule.check("card_1") is False


def test_events_older_than_window_drop_out():
  clock = FakeClock()
  rule = VelocityRule(window_sec=60, max_events=3, now=clock)
  for _ in range(3):
    rule.check("card_1")
  clock.advance(61)  # окно прокатилось мимо первых трёх событий
  assert rule.check("card_1") is True


def test_keys_are_independent():
  clock = FakeClock()
  rule = VelocityRule(window_sec=60, max_events=2, now=clock)
  assert rule.check("card_1") is True
  assert rule.check("card_2") is True
  assert rule.check("card_1") is True
  assert rule.check("card_2") is True
  assert rule.check("card_1") is False
  assert rule.check("card_2") is False


def test_denied_attempts_still_count_toward_the_window():
  """Если бы отказ не считался, атака бы обошла проверку, перебирая после."""
  clock = FakeClock()
  rule = VelocityRule(window_sec=60, max_events=2, now=clock)
  rule.check("ip_x")  # allowed
  rule.check("ip_x")  # allowed
  rule.check("ip_x")  # denied, но засчитано
  rule.check("ip_x")  # denied, тоже засчитано
  # Окно должно прокатиться мимо всех четырёх событий.
  clock.advance(61)
  assert rule.check("ip_x") is True
  assert rule.check("ip_x") is True
  assert rule.check("ip_x") is False


def test_partial_window_decay():
  """Часть событий выходит из окна, часть остаётся."""
  clock = FakeClock()
  rule = VelocityRule(window_sec=60, max_events=2, now=clock)
  rule.check("card_1")  # t=0
  clock.advance(30)
  rule.check("card_1")  # t=30
  clock.advance(31)  # t=61: первое событие вышло, второе ещё в окне
  assert rule.check("card_1") is True  # допустимо: два в окне (t=30, t=61)
  assert rule.check("card_1") is False  # три в окне -- отказ
