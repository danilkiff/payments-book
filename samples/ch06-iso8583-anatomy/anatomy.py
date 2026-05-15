"""Полный разбор MTI 0100 из главы 5.

Схема каждого поля выведена из прозы главы (Шаг 4 раздела
`Разбираем MTI 0100 и MTI 0110 до конца`), а не из общих знаний про
ISO 8583. Это даёт самодостаточный, проверяемый парсер: длины и
форматы зафиксированы в SCHEMA, парсер выдаёт offset/length/value,
тесты сверяют декодированные значения с ожиданиями из главы.
"""

from dataclasses import dataclass


# Hex-дамп MTI 0100 из ch06-iso8583.tex, секция `Разбираем MTI 0100
# и MTI 0110 до конца`. Все поля в ASCII.
CANONICAL_HEX = """
  30 31 30 30
  72 3C 04 81 20 C0 80 00
  31 36 32 32 30 30 31 32 31 32 33 34 35 36 30 38 39 32
  30 30 30 30 30 30
  30 30 30 30 30 30 31 32 35 30 35 30
  30 33 31 37 31 37 33 30 34 35
  34 38 32 37 33 31
  31 37 33 30 34 35
  30 33 31 37
  32 36 31 32
  30 37 31
  30 30
  30 36 31 32 33 34 35 36
  33 34 32 32 30 30 31 32 31 32 33 34 35 36 30 38 39 32
  3D 32 36 31 32 32 30 31 31 32 33 34 35 36 37 38 39 30
  54 45 52 4D 30 30 30 31
  4D 45 52 43 48 41 4E 54 30 30 30 30 30 30 31
  36 34 33
"""
CANONICAL = bytes.fromhex(CANONICAL_HEX)


@dataclass
class Field:
  name: str
  offset: int
  length: int
  raw: bytes
  ll_len: int  # 2 для LLVAR, 0 для fixed
  kind: str  # "mti", "bitmap", "fixed", "llvar"

  @property
  def value(self) -> bytes:
    """Значение без LL-префикса (для LLVAR) или весь chunk (для fixed)."""
    return self.raw[self.ll_len :]


# Схема. Источник длин и форматов -- проза главы 5.5:
#   Шаг 1: MTI = 4 байта ASCII ("0100")
#   Шаг 2: bitmap = 8 байт ("72 3C 04 81 20 C0 80 00")
#   Шаг 3: DE 2 = LLVAR (LL=16, value = 16 цифр PAN)
#   Шаг 4: DE 3=000000 (6), DE 4=000000125050 (12), DE 7=0317173045 (10),
#          DE 11=482731 (6), DE 12=173045 (6), DE 13=0317 (4), DE 14=2612 (4),
#          DE 22=071 (3), DE 25=00 (2), DE 32=123456 (LLVAR, LL=06),
#          DE 35: Track 2 (LLVAR), DE 41=TERM0001 (8),
#          DE 42=MERCHANT0000001 (15), DE 49=643 (3)
SCHEMA = (
  ("MTI", "fixed", 4, "mti"),
  ("Bitmap", "fixed", 8, "bitmap"),
  ("DE 2 (PAN)", "llvar", None, "llvar"),
  ("DE 3 (Proc Code)", "fixed", 6, "fixed"),
  ("DE 4 (Amount)", "fixed", 12, "fixed"),
  ("DE 7 (Trans DT)", "fixed", 10, "fixed"),
  ("DE 11 (STAN)", "fixed", 6, "fixed"),
  ("DE 12 (Local Time)", "fixed", 6, "fixed"),
  ("DE 13 (Local Date)", "fixed", 4, "fixed"),
  ("DE 14 (Expiry)", "fixed", 4, "fixed"),
  ("DE 22 (POS Entry)", "fixed", 3, "fixed"),
  ("DE 25 (POS Cond)", "fixed", 2, "fixed"),
  ("DE 32 (Acq Inst)", "llvar", None, "llvar"),
  ("DE 35 (Track 2)", "llvar", None, "llvar"),
  ("DE 41 (Terminal)", "fixed", 8, "fixed"),
  ("DE 42 (Merchant)", "fixed", 15, "fixed"),
  ("DE 49 (Currency)", "fixed", 3, "fixed"),
)


def parse(message: bytes, schema=SCHEMA) -> list[Field]:
  """Разбирает сообщение по schema. Возвращает список полей с offset/length/raw.

  Для LLVAR-полей читает 2-байтовый ASCII-префикс длины. Не делает
  никаких предположений сверх схемы: схема -- единственный источник
  истины для длин и форматов.
  """
  out: list[Field] = []
  offset = 0
  for name, kind, size, palette in schema:
    start = offset
    if kind == "fixed":
      raw = message[offset : offset + size]
      offset += size
      ll_len = 0
    elif kind == "llvar":
      length = int(message[offset : offset + 2].decode("ascii"))
      raw = message[offset : offset + 2 + length]
      offset += 2 + length
      ll_len = 2
    else:
      raise ValueError(f"unknown kind: {kind}")
    out.append(
      Field(
        name=name,
        offset=start,
        length=len(raw),
        raw=raw,
        ll_len=ll_len,
        kind=palette,
      )
    )
  return out


def bitmap_to_de_numbers(bitmap: bytes) -> list[int]:
  """Раскладывает 8-байтовую primary bitmap в список номеров присутствующих DE.

  Бит 1 -- флаг расширения (secondary bitmap), не DE.
  """
  present = []
  for byte_idx, byte in enumerate(bitmap):
    for bit_idx in range(8):
      if byte & (1 << (7 - bit_idx)):
        de = byte_idx * 8 + bit_idx + 1
        if de != 1:
          present.append(de)
  return present
