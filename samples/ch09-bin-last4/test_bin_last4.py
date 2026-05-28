from itertools import product

import pytest

import bin_last4
from bin_last4 import luhn_valid, tokenize_by_bin_tail

FPAN = "4111111111111111"
BIN_LENGTH = 8
TAIL_LENGTH = 4


def _stub_randbelow(monkeypatch, digits: str):
  stream = iter(digits)
  monkeypatch.setattr(bin_last4.secrets, "randbelow", lambda _n: int(next(stream)))


def test_luhn_valid_recognises_canonical_pan():
  assert luhn_valid(FPAN)
  assert not luhn_valid("4111111111111112")


def test_free_digit_count_matches_brute_force():
  fixed_bin = "415"
  fixed_tail = "27"
  free = 3
  brute = sum(
    1
    for middle in product("0123456789", repeat=free)
    if luhn_valid(fixed_bin + "".join(middle) + fixed_tail)
  )
  assert brute == 10 ** (free - 1)


def test_tokenization_preserves_original_bin_and_tail(monkeypatch):
  _stub_randbelow(monkeypatch, "123")

  token_pan = tokenize_by_bin_tail(FPAN, BIN_LENGTH, TAIL_LENGTH)

  assert token_pan[:BIN_LENGTH] == FPAN[:BIN_LENGTH]
  assert token_pan[-TAIL_LENGTH:] == FPAN[-TAIL_LENGTH:]
  assert token_pan != FPAN
  assert luhn_valid(token_pan)


def test_two_tokens_for_same_fpan_keep_same_bin_and_tail(monkeypatch):
  _stub_randbelow(monkeypatch, "123765")

  first = tokenize_by_bin_tail(FPAN, BIN_LENGTH, TAIL_LENGTH)
  second = tokenize_by_bin_tail(FPAN, BIN_LENGTH, TAIL_LENGTH)

  assert first != second
  assert first[:BIN_LENGTH] == second[:BIN_LENGTH] == FPAN[:BIN_LENGTH]
  assert first[-TAIL_LENGTH:] == second[-TAIL_LENGTH:] == FPAN[-TAIL_LENGTH:]


def test_two_leaks_join_without_pan_or_vault(monkeypatch):
  _stub_randbelow(monkeypatch, "123765")

  first = tokenize_by_bin_tail(FPAN, BIN_LENGTH, TAIL_LENGTH)
  second = tokenize_by_bin_tail(FPAN, BIN_LENGTH, TAIL_LENGTH)
  leak_a = {"merchant_a_token_42": first}
  leak_b = {"psp_b_token_xyz": second}

  joined = [
    (a, b)
    for a, token_a in leak_a.items()
    for b, token_b in leak_b.items()
    if token_a[:BIN_LENGTH] == token_b[:BIN_LENGTH]
    and token_a[-TAIL_LENGTH:] == token_b[-TAIL_LENGTH:]
  ]

  assert joined == [("merchant_a_token_42", "psp_b_token_xyz")]


def test_invalid_fpan_is_rejected():
  with pytest.raises(ValueError):
    tokenize_by_bin_tail("4111111111111112", BIN_LENGTH, TAIL_LENGTH)


def test_mask_without_free_digits_is_rejected():
  with pytest.raises(ValueError):
    tokenize_by_bin_tail(FPAN, bin_length=12, tail_length=4)


def test_lengths_are_parameters(monkeypatch):
  _stub_randbelow(monkeypatch, "11111")

  token_pan = tokenize_by_bin_tail(FPAN, bin_length=6, tail_length=4)

  assert token_pan[:6] == FPAN[:6]
  assert token_pan[-4:] == FPAN[-4:]
  assert luhn_valid(token_pan)
