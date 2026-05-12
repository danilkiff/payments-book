from screening import normalize, screen


def test_normalize_strips_diacritics():
  assert normalize("Müller") == "muller"
  assert normalize("Naïve") == "naive"
  assert normalize("Pão de açúcar") == "paodeacucar"


def test_normalize_lowercases():
  assert normalize("ABC") == "abc"
  assert normalize("ИВАН") == "иван"


def test_normalize_strips_nonalphanumeric():
  assert normalize("O'Brien") == "obrien"
  assert normalize("Иван Петров") == "иванпетров"
  assert normalize("X-Men, Inc.") == "xmeninc"


def test_normalize_empty_input():
  assert normalize("") == ""
  assert normalize("   ") == ""
  assert normalize("!!!---") == ""


def test_exact_match_scores_one():
  hits = screen("Müller", ["Müller"], threshold=0.85)
  assert len(hits) == 1
  assert hits[0].candidate == "Müller"
  assert hits[0].score == 1.0


def test_diacritic_variant_still_matches():
  hits = screen("Muller", ["Müller"], threshold=0.85)
  assert len(hits) == 1


def test_case_variant_still_matches():
  hits = screen("ИВАН ПЕТРОВ", ["иван петров"], threshold=0.85)
  assert len(hits) == 1


def test_unrelated_name_not_matched():
  hits = screen("Smith", ["Иванов"], threshold=0.85)
  assert hits == []


def test_one_char_typo_matches_at_default_threshold():
  # "petov" -- "petrov" без 'r'. Ratio = 2*5/(5+6) = 10/11 ~ 0.91, выше 0.85.
  hits = screen("Petrov", ["Petov"], threshold=0.85)
  assert len(hits) == 1


def test_unrelated_below_threshold_filtered():
  hits = screen("Petrov", ["Sidorov"], threshold=0.85)
  assert hits == []


def test_empty_query_returns_no_hits():
  hits = screen("", ["Müller", "Petrov"], threshold=0.5)
  assert hits == []


def test_empty_watchlist_returns_no_hits():
  hits = screen("Petrov", [], threshold=0.85)
  assert hits == []


def test_multiple_candidates_filtered_by_threshold():
  hits = screen("Petrov", ["Petrov", "Petrov-Vodkin", "Smith"], threshold=0.5)
  candidates = {h.candidate for h in hits}
  assert "Petrov" in candidates
  assert "Smith" not in candidates


def test_low_threshold_admits_partial_match():
  # "iv" vs "ivan": ratio = 2*2/(2+4) = 0.667, выше 0.5.
  hits = screen("Iv", ["Ivan"], threshold=0.5)
  assert len(hits) == 1


def test_high_threshold_admits_only_near_exact():
  hits = screen("Ivan", ["Ivan", "Ivann", "Iv"], threshold=0.95)
  candidates = {h.candidate for h in hits}
  assert "Ivan" in candidates
  # "Ivann" vs "Ivan": ratio = 2*4/(4+5) ~ 0.889, ниже 0.95.
  assert "Ivann" not in candidates
  assert "Iv" not in candidates
