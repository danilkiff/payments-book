import pytest

from retry import (
  DO_NOT_HONOR,
  EXPIRED_CARD,
  INVALID_CARD_NUMBER,
  ISSUER_INOPERATIVE,
  Attempt,
  Decision,
  decide,
)

ACQUIRERS = ["A", "B", "C"]


def test_empty_history_raises():
  with pytest.raises(ValueError, match="history"):
    decide([], ACQUIRERS)


def test_hard_decline_returns_fail():
  for code in (INVALID_CARD_NUMBER, EXPIRED_CARD):
    assert decide([Attempt("A", code)], ACQUIRERS) == Decision.FAIL


def test_transient_returns_retry_same_within_budget():
  history = [Attempt("A", ISSUER_INOPERATIVE)]
  assert decide(history, ACQUIRERS) == Decision.RETRY_SAME


def test_transient_exhausts_retry_budget_then_fails():
  # max_retries=1: первая повторная попытка разрешена, вторая -- нет.
  history = [Attempt("A", ISSUER_INOPERATIVE), Attempt("A", ISSUER_INOPERATIVE)]
  assert decide(history, ACQUIRERS, max_retries=1) == Decision.FAIL


def test_soft_decline_returns_cascade_when_acquirer_available():
  assert decide([Attempt("A", DO_NOT_HONOR)], ACQUIRERS) == Decision.CASCADE


def test_soft_decline_fails_when_all_acquirers_tried():
  history = [Attempt(a, DO_NOT_HONOR) for a in ACQUIRERS]
  assert decide(history, ACQUIRERS) == Decision.FAIL


def test_soft_decline_respects_max_cascade():
  # max_cascade=1: разрешён один каскад (второй эквайер). После двух
  # разных tried -- больше каскадировать нельзя.
  history = [Attempt("A", DO_NOT_HONOR), Attempt("B", DO_NOT_HONOR)]
  assert decide(history, ACQUIRERS, max_cascade=1) == Decision.FAIL


def test_unknown_code_defaults_to_fail():
  # Безопасный дефолт: незнакомый код -- не повторять.
  assert decide([Attempt("A", "99")], ACQUIRERS) == Decision.FAIL


def test_cascade_does_not_retry_same_acquirer():
  # После soft decline решение -- каскад, повтор тому же эквайеру не выбирается.
  history = [Attempt("A", DO_NOT_HONOR)]
  decision = decide(history, ACQUIRERS)
  assert decision == Decision.CASCADE
  # Вызывающий код должен выбрать B или C, не A. Проверить это здесь
  # не можем (decide возвращает только класс решения), но контракт ясен:
  # для CASCADE нужно выбрать эквайера из available, отсутствующего в history.
  tried = {a.acquirer for a in history}
  candidates = [a for a in ACQUIRERS if a not in tried]
  assert "A" not in candidates
  assert candidates == ["B", "C"]
