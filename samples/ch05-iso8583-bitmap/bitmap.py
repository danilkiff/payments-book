from collections.abc import Iterable

MTI_SIZE = 4
BITMAP_SIZE = 8
PRIMARY_START = MTI_SIZE
SECONDARY_START = PRIMARY_START + BITMAP_SIZE


def parse_mti(message: bytes) -> str:
  if len(message) < MTI_SIZE:
    raise ValueError("сообщение короче 4 байт -- MTI не извлечь")
  return message[:MTI_SIZE].decode("ascii")


def parse_bitmap(message: bytes) -> list[int]:
  primary = message[PRIMARY_START:SECONDARY_START]
  if len(primary) < BITMAP_SIZE:
    raise ValueError("primary bitmap должен занимать 8 байт")

  # Старший бит primary -- флаг расширения, а не DE 1.
  has_secondary = bool(primary[0] & 0b1000_0000)
  # Развёртка primary даёт кандидаты на DE 1..64; отбрасываем DE 1 -- это флаг.
  present = [de for de in _bits_to_de_numbers(primary, offset=0) if de != 1]

  if has_secondary:
    secondary = message[SECONDARY_START : SECONDARY_START + BITMAP_SIZE]
    if len(secondary) < BITMAP_SIZE:
      raise ValueError("secondary bitmap ожидается, но не помещается")
    present.extend(_bits_to_de_numbers(secondary, offset=64))
  return present


def _bits_to_de_numbers(block: bytes, offset: int) -> Iterable[int]:
  for byte_index, byte in enumerate(block):
    # f"{byte:08b}" -- строка из 8 битов, от старшего к младшему: "01110010".
    # Позиция в строке = номер бита в байте, бит "1" -- DE присутствует.
    for bit_index, bit in enumerate(f"{byte:08b}"):
      if bit == "1":
        yield offset + byte_index * 8 + bit_index + 1
