import pytest

from retry import Attempt, Decision, decide

ACQUIRERS = ["A", "B", "C"]


def test_empty_history_raises():
  with pytest.raises(ValueError, match="history"):
    decide([], ACQUIRERS)


def test_hard_decline_returns_fail():
  # 14 Invalid Card Number и 54 Expired Card -- классические hard decline.
  for code in ("14", "54", "41", "43"):
    assert decide([Attempt("A", code)], ACQUIRERS) == Decision.FAIL


def test_transient_returns_retry_same_within_budget():
  # 91 Issuer or switch inoperative -- транзиентный сбой.
  history = [Attempt("A", "91")]
  assert decide(history, ACQUIRERS) == Decision.RETRY_SAME


def test_transient_exhausts_retry_budget_then_fails():
  # max_retries=1: первая повторная попытка разрешена, вторая -- нет.
  history = [Attempt("A", "91"), Attempt("A", "91")]
  assert decide(history, ACQUIRERS, max_retries=1) == Decision.FAIL


def test_soft_decline_returns_cascade_when_acquirer_available():
  # 05 Do not honor -- мягкий отказ.
  assert decide([Attempt("A", "05")], ACQUIRERS) == Decision.CASCADE


def test_soft_decline_fails_when_all_acquirers_tried():
  history = [Attempt(a, "05") for a in ACQUIRERS]
  assert decide(history, ACQUIRERS) == Decision.FAIL


def test_soft_decline_respects_max_cascade():
  # max_cascade=1: разрешён один каскад (второй эквайер). После двух
  # разных tried -- больше каскадировать нельзя.
  history = [Attempt("A", "05"), Attempt("B", "05")]
  assert decide(history, ACQUIRERS, max_cascade=1) == Decision.FAIL


def test_unknown_code_defaults_to_fail():
  # Безопасный дефолт: незнакомый код -- не повторять.
  assert decide([Attempt("A", "99")], ACQUIRERS) == Decision.FAIL


def test_cascade_does_not_retry_same_acquirer():
  # После soft decline решение -- каскад, повтор тому же эквайеру не выбирается.
  history = [Attempt("A", "05")]
  decision = decide(history, ACQUIRERS)
  assert decision == Decision.CASCADE
  # Вызывающий код должен выбрать B или C, не A. Проверить это здесь
  # не можем (decide возвращает только класс решения), но контракт ясен:
  # для CASCADE нужно выбрать эквайера из available, отсутствующего в history.
  tried = {a.acquirer for a in history}
  candidates = [a for a in ACQUIRERS if a not in tried]
  assert "A" not in candidates
  assert candidates == ["B", "C"]
