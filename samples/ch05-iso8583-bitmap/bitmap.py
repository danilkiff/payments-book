from collections.abc import Iterable

BITMAP_SIZE = 8


def parse_mti(message: bytes) -> str:
  if len(message) < 4:
    raise ValueError("сообщение короче 4 байт -- MTI не извлечь")
  return message[:4].decode("ascii")


def parse_bitmap(message: bytes) -> list[int]:
  primary = message[4 : 4 + BITMAP_SIZE]
  if len(primary) < BITMAP_SIZE:
    raise ValueError("primary bitmap должен занимать 8 байт")

  # Бит 1 primary -- флаг расширения, а не DE.
  has_secondary = bool(primary[0] & 0x80)
  present = [de for de in _bits_to_de_numbers(primary, offset=0) if de != 1]

  if has_secondary:
    secondary = message[4 + BITMAP_SIZE : 4 + 2 * BITMAP_SIZE]
    if len(secondary) < BITMAP_SIZE:
      raise ValueError("secondary bitmap ожидается, но не помещается")
    present.extend(_bits_to_de_numbers(secondary, offset=64))
  return present


def _bits_to_de_numbers(block: bytes, offset: int) -> Iterable[int]:
  for byte_index, byte in enumerate(block):
    for bit_in_byte in range(8):
      if byte & (0x80 >> bit_in_byte):
        yield offset + byte_index * 8 + bit_in_byte + 1
