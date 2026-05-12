from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class VelocityRule:
  window_sec: float
  max_events: int
  now: Callable[[], float]
  _events: defaultdict[str, deque[float]] = field(
    default_factory=lambda: defaultdict(deque)
  )

  def check(self, key: str) -> bool:
    timeline = self._events[key]
    now = self.now()
    cutoff = now - self.window_sec
    while timeline and timeline[0] < cutoff:
      timeline.popleft()
    timeline.append(now)
    return len(timeline) <= self.max_events
