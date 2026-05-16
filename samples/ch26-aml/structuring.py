"""Алгоритмы детекции дробления (structuring) для главы ch26-aml.

Реализуют три rule-based паттерна, прямо обязательных по
методическим рекомендациям Банка России 19-МР от 21.07.2017:
sub-threshold velocity, fan-out, fan-in. Скользящие окна,
без внешних зависимостей. Источник времени вынесен в события;
тест передаёт детерминированные ts, прод -- time.monotonic.

Graph-based детекция (gather-scatter, scatter-gather, simple
cycle и прочие сложные сети из GARG-AML, arXiv 2506.04292)
в этом модуле не реализована: она требует анализа графа
транзакций, описание принципа -- в основном тексте главы.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Literal

HARD_THRESHOLD_KOPECKS = 1_000_000_00  # статья 6 115-ФЗ
HALF_THRESHOLD_KOPECKS = 500_000_00


@dataclass(frozen=True)
class Event:
  ts: float  # секунды от эпохи; источник времени -- параметр вызывающей системы
  source: str  # счёт отправителя
  destination: str  # счёт получателя
  amount_kopecks: int


Kind = Literal["sub_threshold", "fan_out", "fan_in"]


@dataclass(frozen=True)
class StructuringHit:
  kind: Kind
  key: str  # счёт, по которому сработал паттерн (source или destination)
  count: int
  total_amount_kopecks: int
  window_sec: float


@dataclass
class SubThresholdVelocity:
  """Sub-threshold velocity: N мелких операций общей суммой выше порога.

  Тревога поднимается, если за окно один счёт совершил count_threshold
  или больше операций общей суммой >= sum_threshold_kopecks при том,
  что каждая отдельная операция меньше hard_threshold_kopecks (порога
  обязательного контроля по статье 6 115-ФЗ).
  """

  window_sec: float
  sum_threshold_kopecks: int
  count_threshold: int
  hard_threshold_kopecks: int = HARD_THRESHOLD_KOPECKS
  _by_source: defaultdict[str, deque[Event]] = field(
    default_factory=lambda: defaultdict(deque)
  )

  def observe(self, ev: Event) -> StructuringHit | None:
    # Операция >= порога обязательного контроля идёт по ст. 6
    # отдельным потоком, не накапливается в детекторе дробления.
    if ev.amount_kopecks >= self.hard_threshold_kopecks:
      return None
    timeline = self._by_source[ev.source]
    cutoff = ev.ts - self.window_sec
    while timeline and timeline[0].ts < cutoff:
      timeline.popleft()
    timeline.append(ev)
    total = sum(e.amount_kopecks for e in timeline)
    if len(timeline) >= self.count_threshold and total >= self.sum_threshold_kopecks:
      return StructuringHit(
        kind="sub_threshold",
        key=ev.source,
        count=len(timeline),
        total_amount_kopecks=total,
        window_sec=self.window_sec,
      )
    return None


@dataclass
class FanOut:
  """Fan-out: один источник переводит небольшие суммы на много счетов.

  Срабатывает, если за окно по одному счёту-отправителю наблюдается
  distinct_destinations_threshold или больше уникальных получателей
  при суммах ниже amount_threshold_kopecks.
  """

  window_sec: float
  distinct_destinations_threshold: int
  amount_threshold_kopecks: int = HALF_THRESHOLD_KOPECKS
  _by_source: defaultdict[str, deque[Event]] = field(
    default_factory=lambda: defaultdict(deque)
  )

  def observe(self, ev: Event) -> StructuringHit | None:
    if ev.amount_kopecks >= self.amount_threshold_kopecks:
      return None
    timeline = self._by_source[ev.source]
    cutoff = ev.ts - self.window_sec
    while timeline and timeline[0].ts < cutoff:
      timeline.popleft()
    timeline.append(ev)
    distinct = {e.destination for e in timeline}
    if len(distinct) >= self.distinct_destinations_threshold:
      return StructuringHit(
        kind="fan_out",
        key=ev.source,
        count=len(distinct),
        total_amount_kopecks=sum(e.amount_kopecks for e in timeline),
        window_sec=self.window_sec,
      )
    return None


@dataclass
class FanIn:
  """Fan-in: много источников шлют небольшие суммы одному получателю.

  Зеркало FanOut: индексируется по destination, считает уникальных
  source-ов.
  """

  window_sec: float
  distinct_sources_threshold: int
  amount_threshold_kopecks: int = HALF_THRESHOLD_KOPECKS
  _by_destination: defaultdict[str, deque[Event]] = field(
    default_factory=lambda: defaultdict(deque)
  )

  def observe(self, ev: Event) -> StructuringHit | None:
    if ev.amount_kopecks >= self.amount_threshold_kopecks:
      return None
    timeline = self._by_destination[ev.destination]
    cutoff = ev.ts - self.window_sec
    while timeline and timeline[0].ts < cutoff:
      timeline.popleft()
    timeline.append(ev)
    distinct = {e.source for e in timeline}
    if len(distinct) >= self.distinct_sources_threshold:
      return StructuringHit(
        kind="fan_in",
        key=ev.destination,
        count=len(distinct),
        total_amount_kopecks=sum(e.amount_kopecks for e in timeline),
        window_sec=self.window_sec,
      )
    return None
