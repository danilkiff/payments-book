"""Проверка PAN по алгоритму Луна.

Алгоритм не криптографический: ловит случайные опечатки и часть
перестановок соседних цифр, не защищает от подбора. Реализация
обходит PAN справа налево, удваивает каждую вторую цифру и складывает
их с поправкой "результат больше 9 -- вычесть 9". См. ch03.
"""


def luhn_valid(pan: str) -> bool:
    total = 0
    double = False
    for ch in reversed(pan):
        digit = int(ch)
        if double:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
        double = not double
    return total % 10 == 0
