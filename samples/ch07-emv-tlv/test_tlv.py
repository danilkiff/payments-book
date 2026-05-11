"""Verification for the EMV BER-TLV parser shown in ch07."""

import pytest

from tlv import TLV, parse_tlv


def test_single_byte_tag_primitive():
  # AID Visa Debit/Credit (Classic): тег 0x4F, длина 7, значение -- AID.
  data = bytes.fromhex("4F07A0000000031010")
  [tlv] = parse_tlv(data)
  assert tlv == TLV(tag=0x4F, value=bytes.fromhex("A0000000031010"))


def test_two_byte_tag_primitive():
  # Amount, Authorized (Numeric): тег 0x9F02, длина 6, 12 цифр BCD.
  data = bytes.fromhex("9F0206000000001000")
  [tlv] = parse_tlv(data)
  assert tlv.tag == 0x9F02
  assert tlv.value == bytes.fromhex("000000001000")
  assert tlv.children == ()


def test_long_form_length_128_bytes():
  long_value = bytes(range(128))
  data = bytes([0x4F, 0x81, 0x80]) + long_value
  [tlv] = parse_tlv(data)
  assert tlv.tag == 0x4F
  assert tlv.value == long_value


def test_constructed_tag_recurses_into_children():
  # Минимальный FCI Template (тег 0x6F) с вложенным AID (тег 0x84).
  aid = bytes.fromhex("A0000000031010")
  inner = bytes([0x84, len(aid)]) + aid
  data = bytes([0x6F, len(inner)]) + inner

  [outer] = parse_tlv(data)
  assert outer.tag == 0x6F
  [child] = outer.children
  assert child.tag == 0x84
  assert child.value == aid


def test_constructed_template_with_nested_template():
  # FCI Template (0x6F) → FCI Proprietary Template (0xA5) → Application Label (0x50).
  label = b"VISA"
  a5 = bytes([0x50, len(label)]) + label
  a5_wrapped = bytes([0xA5, len(a5)]) + a5
  aid = bytes.fromhex("A0000000031010")
  aid_wrapped = bytes([0x84, len(aid)]) + aid
  inner = aid_wrapped + a5_wrapped
  data = bytes([0x6F, len(inner)]) + inner

  [outer] = parse_tlv(data)
  assert outer.tag == 0x6F
  assert len(outer.children) == 2
  assert outer.children[0].tag == 0x84
  assert outer.children[1].tag == 0xA5
  [label_tlv] = outer.children[1].children
  assert label_tlv.tag == 0x50
  assert label_tlv.value == label


def test_two_tlvs_in_sequence():
  data = bytes.fromhex("4F07A0000000031010" + "9F0206000000001000")
  tlvs = parse_tlv(data)
  assert [t.tag for t in tlvs] == [0x4F, 0x9F02]


def test_truncated_value_raises():
  # Заявлена длина 10, доступно 3 байта.
  data = bytes.fromhex("4F0AA00000")
  with pytest.raises(ValueError, match="больше остатка"):
    parse_tlv(data)


def test_truncated_multibyte_tag_raises():
  # Первый байт 0x9F намекает на продолжение, но потока больше нет.
  with pytest.raises(ValueError, match="многобайтовом теге"):
    parse_tlv(bytes([0x9F]))


def test_invalid_long_form_length_raises():
  # Long-form говорит "далее 2 байта длины", но в потоке нет ни одного.
  with pytest.raises(ValueError, match="long-form"):
    parse_tlv(bytes([0x4F, 0x82]))
