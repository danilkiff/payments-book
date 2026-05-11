from dataclasses import dataclass, field


@dataclass(frozen=True)
class TLV:
  tag: int
  value: bytes
  children: tuple[TLV, ...] = field(default_factory=tuple)


def parse_tlv(data: bytes) -> list[TLV]:
  result: list[TLV] = []
  cursor = 0
  while cursor < len(data):
    tag, cursor = _read_tag(data, cursor)
    length, cursor = _read_length(data, cursor)
    if cursor + length > len(data):
      raise ValueError(f"тег {tag:X}: длина {length} больше остатка")
    value = data[cursor : cursor + length]
    cursor += length
    children = tuple(parse_tlv(value)) if _is_constructed(tag) else ()
    result.append(TLV(tag, value, children))
  return result


def _read_tag(data: bytes, cursor: int) -> tuple[int, int]:
  first = data[cursor]
  cursor += 1
  # Тег многобайтовый, если младшие 5 бит первого байта = 11111.
  if first & 0x1F != 0x1F:
    return first, cursor
  tag = first
  while cursor < len(data):
    b = data[cursor]
    cursor += 1
    tag = (tag << 8) | b
    if not b & 0x80:  # бит 8 = 0 в последнем байте тега
      return tag, cursor
  raise ValueError("неожиданный конец потока в многобайтовом теге")


def _read_length(data: bytes, cursor: int) -> tuple[int, int]:
  first = data[cursor]
  cursor += 1
  if first < 0x80:
    return first, cursor
  # Long form: первый байт = 0x80 | N, дальше N байт значения длины.
  n = first & 0x7F
  if n == 0 or cursor + n > len(data):
    raise ValueError("некорректная long-form длина")
  length = int.from_bytes(data[cursor : cursor + n], "big")
  return length, cursor + n


def _is_constructed(tag: int) -> bool:
  # Бит 6 первого байта тега = 1 у constructed-тегов (FCI, шаблоны).
  leading = tag
  while leading > 0xFF:
    leading >>= 8
  return bool(leading & 0x20)
