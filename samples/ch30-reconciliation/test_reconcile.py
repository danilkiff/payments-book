from reconcile import Record, reconcile

DAY = 86_400


def test_empty_inputs():
  result = reconcile([], [])
  assert result.matched == []
  assert result.only_internal == []
  assert result.only_external == []


def test_strict_match_by_reference_amount_currency():
  i = Record(reference="REF1", amount=10_000, currency="RUB", ts=0)
  e = Record(reference="REF1", amount=10_000, currency="RUB", ts=0)
  result = reconcile([i], [e])
  assert result.matched == [(i, e)]
  assert result.only_internal == []
  assert result.only_external == []


def test_mismatched_amount_not_matched():
  i = Record("REF1", 10_000, "RUB", 0)
  e = Record("REF1", 10_100, "RUB", 0)  # +1 руб разница
  result = reconcile([i], [e])
  assert result.matched == []
  assert result.only_internal == [i]
  assert result.only_external == [e]


def test_currency_mismatch_not_matched():
  i = Record("REF1", 10_000, "RUB", 0)
  e = Record("REF1", 10_000, "USD", 0)
  result = reconcile([i], [e])
  assert result.matched == []


def test_late_presentment_caught_by_soft_pass():
  # Авторизация ссылается по RRN, клиринг -- по ARN; ссылки не совпали,
  # сумма та же, дата в пределах +-2 дней.
  i = Record("AUTH_RRN", 10_000, "RUB", ts=0)
  e = Record("CLEARING_ARN", 10_000, "RUB", ts=1.5 * DAY)
  result = reconcile([i], [e])
  assert result.matched == [(i, e)]


def test_too_late_presentment_not_matched():
  i = Record("AUTH_RRN", 10_000, "RUB", ts=0)
  e = Record("CLEARING_ARN", 10_000, "RUB", ts=3 * DAY)  # за пределами soft-окна
  result = reconcile([i], [e])
  assert result.matched == []
  assert result.only_internal == [i]
  assert result.only_external == [e]


def test_duplicate_external_records_only_one_matches():
  # Эквайер прислал дубль; матчится только один.
  i = Record("REF1", 10_000, "RUB", 0)
  dup1 = Record("REF1", 10_000, "RUB", 0)
  dup2 = Record("REF1", 10_000, "RUB", 0)
  result = reconcile([i], [dup1, dup2])
  assert len(result.matched) == 1
  assert len(result.only_external) == 1


def test_clearing_without_auth():
  e = Record("REF1", 10_000, "RUB", 0)
  result = reconcile([], [e])
  assert result.matched == []
  assert result.only_external == [e]


def test_auth_without_clearing():
  i = Record("REF1", 10_000, "RUB", 0)
  result = reconcile([i], [])
  assert result.matched == []
  assert result.only_internal == [i]


def test_strict_pass_does_not_steal_records_from_soft_pass():
  # Два внутренних: один с известной ссылкой, один с другой. Два
  # внешних: один с той же ссылкой, один с другой. Должны сматчиться
  # обе пары: первая в строгом проходе, вторая в мягком.
  i1 = Record("REF1", 10_000, "RUB", 0)
  i2 = Record("REF_X", 20_000, "RUB", 0)
  e1 = Record("REF1", 10_000, "RUB", 0)
  e2 = Record("REF_Y", 20_000, "RUB", 100)
  result = reconcile([i1, i2], [e1, e2])
  assert len(result.matched) == 2
  assert (i1, e1) in result.matched
  assert (i2, e2) in result.matched


def test_soft_pass_picks_closest_by_time():
  # Один внутренний, два внешних с той же суммой и валютой,
  # разной датой. Должен выбраться ближайший по времени.
  i = Record("AUTH_RRN", 10_000, "RUB", ts=0)
  far = Record("CLR_FAR", 10_000, "RUB", ts=1.5 * DAY)
  near = Record("CLR_NEAR", 10_000, "RUB", ts=0.5 * DAY)
  result = reconcile([i], [far, near])
  assert result.matched == [(i, near)]
  assert result.only_external == [far]
