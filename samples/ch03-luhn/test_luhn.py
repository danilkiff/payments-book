"""Verification for the Luhn check shown in ch03."""

import pytest

from luhn import luhn_valid


def test_canonical_example_from_chapter_fails():
    # 4561261234560892: вымышленный номер из ch03, контрольная сумма 67.
    # Не должен проходить проверку (67 % 10 != 0).
    assert luhn_valid("4561261234560892") is False


def test_known_valid_test_pans_pass():
    # Стандартные тестовые PAN от Visa/Mastercard/Amex.
    valid = [
        "4111111111111111",  # Visa test PAN
        "5500000000000004",  # Mastercard test PAN
        "340000000000009",  # American Express test PAN
        "6011000000000004",  # Discover test PAN
        "79927398713",  # классический пример из патента Луна
    ]
    for pan in valid:
        assert luhn_valid(pan), f"PAN {pan} должен проходить проверку"


def test_single_digit_typo_is_caught():
    # Изменение одной цифры валидного PAN ломает контрольную сумму.
    valid = "4111111111111111"
    for i in range(len(valid)):
        for replacement in "0123456789":
            if replacement == valid[i]:
                continue
            broken = valid[:i] + replacement + valid[i + 1 :]
            assert not luhn_valid(broken), (
                f"опечатка в позиции {i}: {broken} должен быть отклонён"
            )


def test_adjacent_swap_is_usually_caught():
    """Перестановка соседних цифр чаще всего ломает контрольную сумму.

    Исключение -- пары, у которых обе цифры дают одинаковый вклад
    после удвоения; они проходят перестановку незаметно (известное
    ограничение алгоритма).
    """
    valid = "4111111111111111"
    detected = 0
    for i in range(len(valid) - 1):
        if valid[i] == valid[i + 1]:
            continue  # одинаковые цифры -- перестановка ничего не меняет
        swapped = list(valid)
        swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
        if not luhn_valid("".join(swapped)):
            detected += 1
    assert detected > 0


def test_empty_string_passes_trivially():
    # Edge case: пустая строка даёт сумму 0, кратную 10.
    assert luhn_valid("") is True


def test_non_digit_input_raises():
    with pytest.raises(ValueError):
        luhn_valid("4111-1111-1111-1111")
