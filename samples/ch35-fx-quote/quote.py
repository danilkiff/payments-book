from collections.abc import Callable
from dataclasses import dataclass, field

# 1 pip = 1/10000 единицы quote-валюты. Хранение в pip-точности
# (целые), а не float, исключает накопление погрешности при цепочках
# конверсий.


@dataclass(frozen=True)
class Quote:
  source: str  # ECB, INTERNAL_TREASURY, REUTERS, ...
  base: str  # ISO 4217: "EUR"
  quote: str  # "USD"
  bid_pips: int  # цена покупки base за quote, в pip
  ask_pips: int  # ask >= bid; spread = ask - bid
  ts: float  # epoch seconds, момент фиксации источника


@dataclass
class QuoteBook:
  now: Callable[[], float]
  ttl_seconds: float
  max_spread_bps: int  # basis points: 100 bps = 1%
  _quotes: list[Quote] = field(default_factory=list)

  def add(self, quote: Quote) -> None:
    self._quotes.append(quote)

  def applicable(self, base: str, quote: str) -> Quote | None:
    cutoff = self.now() - self.ttl_seconds
    best: Quote | None = None
    for q in self._quotes:
      if q.base != base or q.quote != quote:
        continue
      if q.ts < cutoff:
        continue
      mid_pips = (q.bid_pips + q.ask_pips) // 2
      if mid_pips <= 0:
        continue
      spread_bps = (q.ask_pips - q.bid_pips) * 10_000 // mid_pips
      if spread_bps > self.max_spread_bps:
        continue
      if best is None or q.ts > best.ts:
        best = q
    return best
