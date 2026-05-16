"""Метрики нечёткого сопоставления имён для главы ch27-sanctions.

Levenshtein -- классическое редакторское расстояние (Левенштейн 1965).
Damerau-Levenshtein -- расширение Дамерау 1964 с транспозицией соседних
символов. Реализация unrestricted DL: транспозиция стоит 1, повторные
правки над одним символом разрешены.
Jaro -- метрика Jaro 1989, чувствительна к позиции совпадений
в окне max(la, lb)/2 - 1.
Jaro-Winkler -- Winkler 1990, добавляет бонус за общий префикс
длиной до четырёх символов с коэффициентом p = 0.1.
"""


def levenshtein(a: str, b: str) -> int:
  if len(a) < len(b):
    a, b = b, a
  if not b:
    return len(a)
  prev = list(range(len(b) + 1))
  for i, ca in enumerate(a, 1):
    curr = [i]
    for j, cb in enumerate(b, 1):
      ins = curr[j - 1] + 1
      delete = prev[j] + 1
      sub = prev[j - 1] + (ca != cb)
      curr.append(min(ins, delete, sub))
    prev = curr
  return prev[-1]


def damerau_levenshtein(a: str, b: str) -> int:
  la, lb = len(a), len(b)
  alphabet = set(a) | set(b)
  inf = la + lb
  d = [[0] * (lb + 2) for _ in range(la + 2)]
  d[0][0] = inf
  for i in range(la + 1):
    d[i + 1][0] = inf
    d[i + 1][1] = i
  for j in range(lb + 1):
    d[0][j + 1] = inf
    d[1][j + 1] = j
  da = dict.fromkeys(alphabet, 0)
  for i in range(1, la + 1):
    db = 0
    for j in range(1, lb + 1):
      k = da[b[j - 1]]
      ell = db
      cost = 0 if a[i - 1] == b[j - 1] else 1
      if cost == 0:
        db = j
      d[i + 1][j + 1] = min(
        d[i][j] + cost,
        d[i + 1][j] + 1,
        d[i][j + 1] + 1,
        d[k][ell] + (i - k - 1) + 1 + (j - ell - 1),
      )
    da[a[i - 1]] = i
  return d[la + 1][lb + 1]


def jaro(a: str, b: str) -> float:
  if a == b:
    return 1.0
  la, lb = len(a), len(b)
  if la == 0 or lb == 0:
    return 0.0
  match_dist = max(la, lb) // 2 - 1
  a_match = [False] * la
  b_match = [False] * lb
  matches = 0
  for i, ca in enumerate(a):
    start = max(0, i - match_dist)
    end = min(i + match_dist + 1, lb)
    for j in range(start, end):
      if b_match[j] or ca != b[j]:
        continue
      a_match[i] = True
      b_match[j] = True
      matches += 1
      break
  if matches == 0:
    return 0.0
  trans = 0
  k = 0
  for i in range(la):
    if not a_match[i]:
      continue
    while not b_match[k]:
      k += 1
    if a[i] != b[k]:
      trans += 1
    k += 1
  trans //= 2
  return (matches / la + matches / lb + (matches - trans) / matches) / 3.0


def jaro_winkler(a: str, b: str, p: float = 0.1, max_l: int = 4) -> float:
  base = jaro(a, b)
  prefix = 0
  for i in range(min(len(a), len(b), max_l)):
    if a[i] != b[i]:
      break
    prefix += 1
  return base + prefix * p * (1 - base)
