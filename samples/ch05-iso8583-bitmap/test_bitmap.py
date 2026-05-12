import pytest

from bitmap import parse_bitmap, parse_mti

# Канонический MTI 0100 + primary bitmap из ch05.
# Парсеру нужны только эти 12 байт; payload после bitmap он не читает.
CANONICAL = bytes.fromhex("30313030" + "723C0481" + "20C08000")


def test_parse_mti_returns_ascii_string():
  assert parse_mti(CANONICAL) == "0100"


def test_parse_bitmap_matches_canonical_de_set():
  assert parse_bitmap(CANONICAL) == [
    2,
    3,
    4,
    7,
    11,
    12,
    13,
    14,
    22,
    25,
    32,
    35,
    41,
    42,
    49,
  ]


def test_empty_bitmap_yields_no_des():
  msg = b"0100" + b"\x00" * 8
  assert parse_bitmap(msg) == []


def test_secondary_bitmap_extends_de_range():
  # Primary: только бит 1 (флаг расширения, не DE).
  # Secondary: бит 1 → DE 65, бит 64 → DE 128.
  primary = bytes([0x80, 0, 0, 0, 0, 0, 0, 0])
  secondary = bytes([0x80, 0, 0, 0, 0, 0, 0, 0x01])
  msg = b"0200" + primary + secondary
  assert parse_bitmap(msg) == [65, 128]


def test_secondary_flag_without_secondary_bytes_raises():
  primary = bytes([0x80, 0, 0, 0, 0, 0, 0, 0])
  msg = b"0100" + primary  # secondary отсутствует
  with pytest.raises(ValueError, match="secondary bitmap"):
    parse_bitmap(msg)


def test_short_message_raises_on_mti():
  with pytest.raises(ValueError, match="MTI"):
    parse_mti(b"010")


def test_short_message_raises_on_bitmap():
  with pytest.raises(ValueError, match="primary bitmap"):
    parse_bitmap(b"0100\x00\x00")
