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
