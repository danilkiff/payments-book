"""Тесты разбора MTI 0100.

Ожидаемые значения взяты из прозы главы 5.5 (Шаг 4). Если парсер
расходится с прозой хоть в одном поле или offset не сходится с длиной
дампа -- тесты падают.
"""

import itertools

import pytest
from anatomy import CANONICAL, bitmap_to_de_numbers, parse


@pytest.fixture
def fields():
  return parse(CANONICAL)


def test_parse_consumes_entire_message(fields):
  total = sum(f.length for f in fields)
  assert total == len(CANONICAL), (
    f"парсер прочитал {total} байт, дамп {len(CANONICAL)} байт"
  )


def test_field_count(fields):
  assert len(fields) == 17  # MTI + Bitmap + 15 DE


# Ожидаемые декодированные значения. Источник -- проза Шага 4 главы 5.5.
EXPECTED_VALUES = {
  "MTI": "0100",
  "DE 2 (PAN)": "2200121234560892",
  "DE 3 (Proc Code)": "000000",
  "DE 4 (Amount)": "000000125050",
  "DE 7 (Trans DT)": "0317173045",
  "DE 11 (STAN)": "482731",
  "DE 12 (Local Time)": "173045",
  "DE 13 (Local Date)": "0317",
  "DE 14 (Expiry)": "2612",
  "DE 22 (POS Entry)": "071",
  "DE 25 (POS Cond)": "00",
  "DE 32 (Acq Inst)": "123456",
  "DE 41 (Terminal)": "TERM0001",
  "DE 42 (Merchant)": "MERCHANT0000001",
  "DE 49 (Currency)": "643",
}


@pytest.mark.parametrize("name,expected", EXPECTED_VALUES.items())
def test_decoded_value_matches_prose(fields, name, expected):
  found = next((f for f in fields if f.name == name), None)
  assert found is not None, f"поле {name} не найдено"
  got = found.value.decode("ascii")
  assert got == expected


def test_bitmap_decodes_to_expected_des(fields):
  bitmap = next(f for f in fields if f.name == "Bitmap")
  des = bitmap_to_de_numbers(bitmap.raw)
  # Те же 15 DE, что в прозе и в test_bitmap.py.
  assert des == [2, 3, 4, 7, 11, 12, 13, 14, 22, 25, 32, 35, 41, 42, 49]


def test_llvar_length_prefix_matches_value(fields):
  for name in ("DE 2 (PAN)", "DE 32 (Acq Inst)", "DE 35 (Track 2)"):
    f = next(field for field in fields if field.name == name)
    declared = int(f.raw[:2].decode("ascii"))
    actual = len(f.value)
    assert declared == actual, (
      f"{name}: LL={declared}, фактическая длина значения={actual}"
    )


def test_offsets_strictly_increase(fields):
  for prev, curr in itertools.pairwise(fields):
    assert curr.offset == prev.offset + prev.length, (
      f"разрыв между {prev.name} и {curr.name}"
    )
