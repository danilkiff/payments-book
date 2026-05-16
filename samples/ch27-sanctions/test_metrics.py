from metrics import damerau_levenshtein, jaro, jaro_winkler, levenshtein


def test_levenshtein_identical_pair_is_zero():
  assert levenshtein("IVANOV", "IVANOV") == 0


def test_levenshtein_one_substitution():
  # YVANOV vs IVANOV: одна замена I→Y.
  assert levenshtein("IVANOV", "YVANOV") == 1


def test_levenshtein_insertion_and_substitution():
  # IVANOFF vs IVANOV: одна замена V→F + вставка F.
  assert levenshtein("IVANOV", "IVANOFF") == 2


def test_levenshtein_counts_transposition_as_two_edits():
  # IVAONV vs IVANOV: перестановка NO ↔ ON стоит 2 в Левенштейне.
  assert levenshtein("IVANOV", "IVAONV") == 2


def test_damerau_levenshtein_counts_adjacent_transposition_as_one():
  # Та же пара в DL: одна транспозиция = 1.
  assert damerau_levenshtein("IVANOV", "IVAONV") == 1


def test_damerau_levenshtein_matches_levenshtein_for_substitutions():
  assert damerau_levenshtein("IVANOV", "YVANOV") == 1


def test_jaro_exact_match_is_one():
  assert jaro("IVANOV", "IVANOV") == 1.0


def test_jaro_no_common_characters_is_zero():
  assert jaro("ИВАНОВ", "IVANOV") == 0.0


def test_jaro_winkler_adds_prefix_bonus():
  # IVANOFF делит с IVANOV префикс IVAN (4 символа), JW > J.
  j = jaro("IVANOV", "IVANOFF")
  jw = jaro_winkler("IVANOV", "IVANOFF")
  assert jw > j


def test_jaro_winkler_zero_when_prefix_differs():
  # YVANOV расходится с IVANOV на первом символе, бонуса нет.
  j = jaro("IVANOV", "YVANOV")
  jw = jaro_winkler("IVANOV", "YVANOV")
  assert jw == j


def test_jaro_winkler_prefix_capped_at_four():
  a = "PETROV-VODKIN"
  b = "PETROVSKII"
  jw = jaro_winkler(a, b)
  jw_capped = jaro_winkler(a, b, max_l=4)
  assert jw == jw_capped
