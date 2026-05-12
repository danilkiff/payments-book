import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass(frozen=True)
class Hit:
  query: str  # как пришло из CMS
  candidate: str  # имя из санкционного перечня
  score: float  # 0..1


def normalize(name: str) -> str:
  # NFKD раскладывает букву с диакритикой на базовую + комбинирующий
  # знак. Например, "ё" -> "е" + диакритика "..".
  decomposed = unicodedata.normalize("NFKD", name)
  # Категория Mn = nonspacing mark (диакритика). Отбрасываем.
  no_diacritics = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
  # Lowercase + только буквы и цифры; пробелы, дефисы, апострофы выпадают.
  return "".join(c.lower() for c in no_diacritics if c.isalnum())


def screen(
  query: str,
  watchlist: list[str],
  threshold: float = 0.85,
) -> list[Hit]:
  q_norm = normalize(query)
  if not q_norm:
    return []
  hits: list[Hit] = []
  for candidate in watchlist:
    c_norm = normalize(candidate)
    if not c_norm:
      continue
    # SequenceMatcher ищет совпадающие блоки алгоритмом Ratcliff-Obershelp;
    # .ratio() -- метрика 2*M/T на этих блоках (M -- сумма их длин,
    # T -- сумма длин обеих строк).
    score = SequenceMatcher(None, q_norm, c_norm).ratio()
    if score >= threshold:
      hits.append(Hit(query=query, candidate=candidate, score=score))
  return hits
