"""Транслитерация кириллицы в латиницу по трём стандартам.

ISO 9:1995 (тождествен ГОСТ 7.79-2000 системе А) -- строгое 1-к-1
с диакритикой; полностью обратима.
BGN/PCGN 1947 -- стандарт США (BGN) и Великобритании (PCGN)
для географических имён и документов. Контекстное правило: е и ё
романизируются как ye / yë в начале слова, после гласных и после
й, ъ, ь.
ICAO Doc 9303 part 3 -- стандарт ИКАО для машиночитаемой зоны
паспорта (MRZ). Использует только базовые латинские буквы A-Z;
ь не передаётся.

Регистр выходной строки повторяет регистр входной по правилу
слова: всё слово в верхнем регистре -- результат в верхнем;
первая заглавная при строчных остальных -- результат capitalize;
иначе строчный.
"""

import re

ISO_9_1995 = {
  "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
  "е": "e", "ё": "ë", "ж": "ž", "з": "z", "и": "i",
  "й": "j", "к": "k", "л": "l", "м": "m", "н": "n",
  "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
  "у": "u", "ф": "f", "х": "h", "ц": "c", "ч": "č",
  "ш": "š", "щ": "ŝ", "ъ": "ʺ", "ы": "y", "ь": "ʹ",
  "э": "è", "ю": "û", "я": "â",
}  # fmt: skip

BGN_PCGN_BASE = {
  "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
  "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k",
  "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
  "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f",
  "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
  "ъ": "ʺ", "ы": "y", "ь": "ʹ", "э": "e", "ю": "yu",
  "я": "ya",
}  # fmt: skip

ICAO_9303 = {
  "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
  "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
  "й": "i", "к": "k", "л": "l", "м": "m", "н": "n",
  "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
  "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
  "ш": "sh", "щ": "shch", "ъ": "ie", "ы": "y", "ь": "",
  "э": "e", "ю": "iu", "я": "ia",
}  # fmt: skip

_BGN_PRECEDING_TRIGGERS_YE = set("аеёиоуыэюяйъь")
_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)


def _apply_word_case(source: str, transformed: str) -> str:
  letters = [c for c in source if c.isalpha()]
  if letters and all(c.isupper() for c in letters):
    return transformed.upper()
  if source and source[0].isupper():
    return transformed[:1].upper() + transformed[1:]
  return transformed


def _by_word(text: str, word_translit) -> str:
  parts: list[str] = []
  last = 0
  for m in _WORD_RE.finditer(text):
    parts.append(text[last : m.start()])
    src = m.group(0)
    parts.append(_apply_word_case(src, word_translit(src.lower())))
    last = m.end()
  parts.append(text[last:])
  return "".join(parts)


def _map_chars(word: str, table: dict[str, str]) -> str:
  return "".join(table.get(c, c) for c in word)


def iso_9(text: str) -> str:
  return _by_word(text, lambda w: _map_chars(w, ISO_9_1995))


def icao_9303(text: str) -> str:
  return _by_word(text, lambda w: _map_chars(w, ICAO_9303))


def _bgn_word(word: str) -> str:
  out: list[str] = []
  for i, c in enumerate(word):
    if c in ("е", "ё"):
      prev = word[i - 1] if i > 0 else ""
      after_trigger = i == 0 or prev in _BGN_PRECEDING_TRIGGERS_YE
      core = "ye" if c == "е" else "yë"
      if not after_trigger:
        core = "e" if c == "е" else "ë"
      out.append(core)
    else:
      out.append(BGN_PCGN_BASE.get(c, c))
  return "".join(out)


def bgn_pcgn(text: str) -> str:
  return _by_word(text, _bgn_word)
