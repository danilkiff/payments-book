from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
  # RRN (DE 37) на стороне авторизации; ARN/Acquirer Reference (DE 31
  # в IPM, эквивалент в BASE II) на стороне клиринга. Реконсилиатору
  # достаточно того, что строка одинаково построена в обоих источниках.
  reference: str
  amount: int  # минорные единицы
  currency: str  # ISO 4217
  ts: float  # epoch seconds


@dataclass
class MatchResult:
  matched: list[tuple[Record, Record]]
  only_internal: list[Record]
  only_external: list[Record]


def reconcile(
  internal: list[Record],
  external: list[Record],
  strict_tolerance: float = 86_400,  # +-1 день
  soft_tolerance: float = 2 * 86_400,  # +-2 дня
) -> MatchResult:
  int_taken = [False] * len(internal)
  ext_taken = [False] * len(external)
  pairs: list[tuple[Record, Record]] = []

  # Проход 1 (строгий): reference + currency + amount, дата в strict_tolerance.
  for i, irec in enumerate(internal):
    for j, erec in enumerate(external):
      if ext_taken[j]:
        continue
      if irec.reference != erec.reference:
        continue
      if irec.amount != erec.amount or irec.currency != erec.currency:
        continue
      if abs(irec.ts - erec.ts) > strict_tolerance:
        continue
      pairs.append((irec, erec))
      int_taken[i] = True
      ext_taken[j] = True
      break

  # Проход 2 (мягкий): currency + amount, дата в soft_tolerance.
  # reference не сравниваем -- авторизационный RRN и клиринговый ARN
  # это разные идентификаторы, и при late presentment их связь теряется.
  # Из подходящих выбираем ближайшую по времени.
  for i, irec in enumerate(internal):
    if int_taken[i]:
      continue
    best_j: int | None = None
    best_delta: float = 0.0
    for j, erec in enumerate(external):
      if ext_taken[j]:
        continue
      if irec.amount != erec.amount or irec.currency != erec.currency:
        continue
      delta = abs(irec.ts - erec.ts)
      if delta > soft_tolerance:
        continue
      if best_j is None or delta < best_delta:
        best_j = j
        best_delta = delta
    if best_j is not None:
      pairs.append((irec, external[best_j]))
      int_taken[i] = True
      ext_taken[best_j] = True

  return MatchResult(
    matched=pairs,
    only_internal=[r for i, r in enumerate(internal) if not int_taken[i]],
    only_external=[r for j, r in enumerate(external) if not ext_taken[j]],
  )
