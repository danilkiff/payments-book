from structuring import Event, FanIn, FanOut, SubThresholdVelocity

WEEK = 7 * 24 * 60 * 60.0


def ev(ts, source="c-1", destination="d-1", amount_kopecks=100_000_00) -> Event:
  return Event(
    ts=ts, source=source, destination=destination, amount_kopecks=amount_kopecks
  )


def test_sub_threshold_velocity_below_count_threshold_no_hit():
  rule = SubThresholdVelocity(
    window_sec=WEEK, sum_threshold_kopecks=1_000_000_00, count_threshold=5
  )
  for i in range(4):
    assert rule.observe(ev(ts=i * 100, amount_kopecks=200_000_00)) is None


def test_sub_threshold_velocity_fires_when_sum_and_count_reached():
  rule = SubThresholdVelocity(
    window_sec=WEEK, sum_threshold_kopecks=1_000_000_00, count_threshold=5
  )
  hits = [rule.observe(ev(ts=i * 100, amount_kopecks=200_000_00)) for i in range(5)]
  assert hits[:4] == [None, None, None, None]
  assert hits[4] is not None
  assert hits[4].kind == "sub_threshold"
  assert hits[4].count == 5
  assert hits[4].total_amount_kopecks == 1_000_000_00


def test_sub_threshold_velocity_ignores_event_above_hard_threshold():
  # Операция >= порога обязательного контроля идёт по ст. 6 напрямую,
  # детектор дробления её не учитывает.
  rule = SubThresholdVelocity(
    window_sec=WEEK, sum_threshold_kopecks=1_000_000_00, count_threshold=5
  )
  assert rule.observe(ev(ts=0, amount_kopecks=1_500_000_00)) is None


def test_sub_threshold_velocity_window_decays():
  rule = SubThresholdVelocity(
    window_sec=100, sum_threshold_kopecks=300_000_00, count_threshold=3
  )
  rule.observe(ev(ts=0, amount_kopecks=100_000_00))
  # t=200 -- первая операция вылетела из окна (cutoff=100).
  rule.observe(ev(ts=200, amount_kopecks=100_000_00))
  rule.observe(ev(ts=210, amount_kopecks=100_000_00))
  hit = rule.observe(ev(ts=220, amount_kopecks=100_000_00))
  assert hit is not None
  assert hit.count == 3


def test_sub_threshold_velocity_keys_are_independent():
  rule = SubThresholdVelocity(
    window_sec=WEEK, sum_threshold_kopecks=300_000_00, count_threshold=3
  )
  for source in ("c-1", "c-2"):
    for i in range(2):
      assert rule.observe(ev(ts=i, source=source, amount_kopecks=100_000_00)) is None


def test_fan_out_fires_on_many_distinct_destinations():
  rule = FanOut(window_sec=WEEK, distinct_destinations_threshold=10)
  hits = [
    rule.observe(ev(ts=i * 60, destination=f"d-{i}", amount_kopecks=100_000_00))
    for i in range(10)
  ]
  assert hits[-1] is not None
  assert hits[-1].kind == "fan_out"
  assert hits[-1].count == 10


def test_fan_out_does_not_count_repeated_destinations():
  rule = FanOut(window_sec=WEEK, distinct_destinations_threshold=3)
  # Один и тот же получатель повторяется пять раз -- distinct остаётся 1.
  hits = [
    rule.observe(ev(ts=i, destination="d-1", amount_kopecks=100_000_00))
    for i in range(5)
  ]
  assert all(h is None for h in hits)


def test_fan_out_ignores_amounts_above_threshold():
  rule = FanOut(window_sec=WEEK, distinct_destinations_threshold=3)
  for i in range(3):
    # 600 тыс. > половины порога ст. 6 -- не дробление.
    assert (
      rule.observe(ev(ts=i, destination=f"d-{i}", amount_kopecks=600_000_00)) is None
    )


def test_fan_in_fires_on_many_distinct_sources():
  rule = FanIn(window_sec=WEEK, distinct_sources_threshold=10)
  hits = [
    rule.observe(
      ev(ts=i * 60, source=f"c-{i}", destination="dest-1", amount_kopecks=100_000_00)
    )
    for i in range(10)
  ]
  assert hits[-1] is not None
  assert hits[-1].kind == "fan_in"
  assert hits[-1].key == "dest-1"


def test_fan_in_independent_destinations():
  rule = FanIn(window_sec=WEEK, distinct_sources_threshold=3)
  # Два разных получателя, по 2 уникальных отправителя у каждого --
  # ни один не достигает порога 3.
  for dest in ("d-A", "d-B"):
    for i in range(2):
      assert (
        rule.observe(
          ev(ts=i, source=f"c-{i}", destination=dest, amount_kopecks=100_000_00)
        )
        is None
      )
