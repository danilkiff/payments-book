from dataclasses import dataclass


@dataclass(frozen=True)
class TLV:
  tag: int
  value: bytes
  children: tuple[TLV, ...] = ()


def parse_tlv(data: bytes) -> list[TLV]:
  result: list[TLV] = []
  cursor = 0
  while cursor < len(data):
    # Бит 6 первого байта тега = 1 у constructed-тегов (FCI, шаблоны).
    is_constructed = bool(data[cursor] & 0b0010_0000)
    tag, cursor = _read_tag(data, cursor)
    length, cursor = _read_length(data, cursor)
    if cursor + length > len(data):
      raise ValueError(f"тег {tag:X}: длина {length} больше остатка")
    value = data[cursor : cursor + length]
    cursor += length
    children = tuple(parse_tlv(value)) if is_constructed else ()
    result.append(TLV(tag, value, children))
  return result


def _read_tag(data: bytes, cursor: int) -> tuple[int, int]:
  first = data[cursor]
  cursor += 1
  # Тег многобайтовый, если младшие 5 бит первого байта = 11111.
  if first & 0b0001_1111 != 0b0001_1111:
    return first, cursor
  tag = first
  while cursor < len(data):
    b = data[cursor]
    cursor += 1
    tag = (tag << 8) | b
    if not b & 0b1000_0000:  # старший бит = 0 в последнем байте тега
      return tag, cursor
  raise ValueError("неожиданный конец потока в многобайтовом теге")


def _read_length(data: bytes, cursor: int) -> tuple[int, int]:
  first = data[cursor]
  cursor += 1
  # Short form: старший бит = 0, остальные 7 бит -- сама длина (0..127).
  if not first & 0b1000_0000:
    return first, cursor
  # Long form: первый байт = 0b1000_0000 | N, дальше N байт значения длины.
  n = first & 0b0111_1111
  if n == 0 or cursor + n > len(data):
    raise ValueError("некорректная long-form длина")
  length = int.from_bytes(data[cursor : cursor + n], "big")
  return length, cursor + n
