from quote import Quote, QuoteBook


class FakeClock:
  def __init__(self, start: float = 0.0) -> None:
    self.t = start

  def __call__(self) -> float:
    return self.t

  def advance(self, seconds: float) -> None:
    self.t += seconds


def make_book(clock: FakeClock, ttl: float = 60, max_spread: int = 100) -> QuoteBook:
  return QuoteBook(now=clock, ttl_seconds=ttl, max_spread_bps=max_spread)


def test_empty_book_returns_none():
  clock = FakeClock()
  assert make_book(clock).applicable("EUR", "USD") is None


def test_fresh_quote_is_returned():
  clock = FakeClock()
  book = make_book(clock)
  q = Quote("ECB", "EUR", "USD", bid_pips=10800, ask_pips=10810, ts=clock())
  book.add(q)
  assert book.applicable("EUR", "USD") is q


def test_quote_older_than_ttl_is_filtered():
  clock = FakeClock()
  book = make_book(clock, ttl=60)
  book.add(Quote("ECB", "EUR", "USD", 10800, 10810, ts=clock()))
  clock.advance(61)
  assert book.applicable("EUR", "USD") is None


def test_among_fresh_quotes_most_recent_wins():
  clock = FakeClock(start=100)
  book = make_book(clock, ttl=60)
  old = Quote("ECB", "EUR", "USD", 10800, 10810, ts=80)
  newer = Quote("INTERNAL", "EUR", "USD", 10805, 10815, ts=95)
  book.add(old)
  book.add(newer)
  assert book.applicable("EUR", "USD") is newer


def test_stale_quote_dropped_fresh_kept():
  clock = FakeClock(start=100)
  book = make_book(clock, ttl=60)
  # cutoff = 40: всё с ts < 40 устарело.
  book.add(Quote("OLD", "EUR", "USD", 10800, 10810, ts=30))
  book.add(Quote("NEW", "EUR", "USD", 10805, 10815, ts=80))
  selected = book.applicable("EUR", "USD")
  assert selected is not None and selected.source == "NEW"


def test_wrong_pair_filtered():
  clock = FakeClock()
  book = make_book(clock)
  book.add(Quote("ECB", "EUR", "GBP", 8700, 8710, ts=clock()))
  assert book.applicable("EUR", "USD") is None


def test_wide_spread_quote_filtered():
  # mid ~ 10000, spread = 200 pip -> 200 bps; max=50 bps -> отказ.
  clock = FakeClock()
  book = make_book(clock, max_spread=50)
  book.add(Quote("WIDE", "EUR", "USD", 9900, 10100, ts=clock()))
  assert book.applicable("EUR", "USD") is None


def test_quote_at_ttl_boundary_passes():
  # ts == cutoff -- ровно на границе, не строго меньше => fresh.
  clock = FakeClock(start=100)
  book = make_book(clock, ttl=60)
  book.add(Quote("EDGE", "EUR", "USD", 10800, 10810, ts=40))
  assert book.applicable("EUR", "USD") is not None
