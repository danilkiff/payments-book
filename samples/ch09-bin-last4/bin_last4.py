import secrets


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


def tokenize_by_bin_tail(
  fpan: str,
  bin_length: int,
  tail_length: int,
) -> str:
  if not fpan.isdecimal() or not luhn_valid(fpan):
    raise ValueError("FPAN должен быть PAN с корректной цифрой Луна")

  free_digits = len(fpan) - bin_length - tail_length
  if free_digits <= 0:
    raise ValueError("маска не оставляет места для случайной части")

  head = fpan[:bin_length]
  tail = fpan[-tail_length:] if tail_length else ""
  middle_prefix = "".join(str(secrets.randbelow(10)) for _ in range(free_digits - 1))

  for last in range(10):
    candidate = head + middle_prefix + str(last) + tail
    if luhn_valid(candidate):
      return candidate
  raise AssertionError("ровно одна цифра из десяти проходит Луна")
