"""Закрепляет числа таблицы tab:sanctions-metrics в ch27-sanctions.tex.

Алгоритмы Левенштейна, Дамерау-Левенштейна, Jaro и Jaro-Winkler берутся
из пакета jellyfish; тесты лишь проверяют, что значения для пар из таблицы
не разойдутся с тем, что напечатано в книге.
"""

import jellyfish as jf
import pytest


@pytest.mark.parametrize(
  ("a", "b", "lev", "dl"),
  [
    ("IVANOV", "IVANOV", 0, 0),
    ("IVANOV", "IVANOFF", 2, 2),
    ("IVANOV", "YVANOV", 1, 1),
    ("IVANOV", "IVAN-OFF", 3, 3),
    ("IVANOV", "IVAONV", 2, 1),
  ],
)
def test_edit_distances_match_table(a: str, b: str, lev: int, dl: int):
  assert jf.levenshtein_distance(a, b) == lev
  assert jf.damerau_levenshtein_distance(a, b) == dl


@pytest.mark.parametrize(
  ("a", "b", "jaro", "jw"),
  [
    ("IVANOV", "IVANOV", 1.000, 1.000),
    ("IVANOV", "IVANOFF", 0.849, 0.910),
    ("IVANOV", "YVANOV", 0.889, 0.889),
    ("IVANOV", "IVAN-OFF", 0.819, 0.892),
    ("IVANOV", "IVAONV", 0.944, 0.961),
  ],
)
def test_jaro_scores_match_table(a: str, b: str, jaro: float, jw: float):
  assert jf.jaro_similarity(a, b) == pytest.approx(jaro, abs=5e-4)
  assert jf.jaro_winkler_similarity(a, b) == pytest.approx(jw, abs=5e-4)


def test_damerau_levenshtein_distinguishes_transposition():
  # Только DL отделяет соседнюю транспозицию NO↔ON от двух независимых правок;
  # этот контраст обсуждается в прозе после таблицы.
  assert jf.levenshtein_distance("IVANOV", "IVAONV") == 2
  assert jf.damerau_levenshtein_distance("IVANOV", "IVAONV") == 1


def test_jaro_winkler_prefix_bonus_for_ivanoff():
  # IVANOFF делит с IVANOV префикс IVAN (4 символа), JW > J.
  base = jf.jaro_similarity("IVANOV", "IVANOFF")
  boosted = jf.jaro_winkler_similarity("IVANOV", "IVANOFF")
  assert boosted > base


def test_jaro_winkler_no_bonus_when_first_char_differs():
  # YVANOV расходится с IVANOV на первом символе, бонус нулевой.
  assert jf.jaro_winkler_similarity("IVANOV", "YVANOV") == jf.jaro_similarity(
    "IVANOV", "YVANOV"
  )
