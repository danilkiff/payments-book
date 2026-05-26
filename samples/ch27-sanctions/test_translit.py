"""Закрепляет ячейки таблицы tab:sanctions-translit в ch27-sanctions.tex.

Транслитерация по трём стандартам берётся из пакета iuliia; тесты
проверяют, что значения для имён из таблицы не разойдутся с тем,
что напечатано в книге.

iuliia в схемах GOST_779 (ISO 9) и BGN_PCGN не переводит кириллическое
Ё/ё в латинское Ë/ё; в обёртках iso_9/bgn_pcgn это исправляется
ручной заменой Ё→Ë. ICAO_DOC_9303 работает без обёртки.
"""

import iuliia
import pytest


def _fix_yo(text: str) -> str:
  return text.replace("ё", "ë").replace("Ё", "Ë")


def iso_9(text: str) -> str:
  return _fix_yo(iuliia.GOST_779.translate(text)).upper()


def bgn_pcgn(text: str) -> str:
  return _fix_yo(iuliia.BGN_PCGN.translate(text)).upper()


def icao_9303(text: str) -> str:
  return iuliia.ICAO_DOC_9303.translate(text).upper()


@pytest.mark.parametrize(
  ("name", "iso9", "bgn", "icao"),
  [
    ("ЕВГЕНИЙ", "EVGENIJ", "YEVGENIY", "EVGENII"),
    ("ЕКАТЕРИНА", "EKATERINA", "YEKATERINA", "EKATERINA"),
    ("ЮРИЙ", "ÛRIJ", "YURIY", "IURII"),
    ("ЦАРЁВ", "CARËV", "TSARËV", "TSAREV"),
    ("ЩУКИН", "ŜUKIN", "SHCHUKIN", "SHCHUKIN"),
    ("ФЁДОРОВ", "FËDOROV", "FËDOROV", "FEDOROV"),
  ],
)
def test_three_systems_match_table(name: str, iso9: str, bgn: str, icao: str):
  assert iso_9(name) == iso9
  assert bgn_pcgn(name) == bgn
  assert icao_9303(name) == icao


def test_bgn_pcgn_ye_at_word_start():
  # Е/Ё в начале слова -> YE/YË (контекстное правило BGN/PCGN).
  assert bgn_pcgn("ЕЛКИН") == "YELKIN"
  assert bgn_pcgn("ЁЛКИН") == "YËLKIN"


def test_bgn_pcgn_ye_after_vowel():
  # Е после гласной -> YE.
  assert bgn_pcgn("ЗАЕВ") == "ZAYEV"


def test_bgn_pcgn_e_after_consonant():
  # Е/Ё после согласной -> E/Ë без y-префикса.
  assert bgn_pcgn("КУЗНЕЦОВ") == "KUZNETSOV"


def test_icao_drops_soft_sign():
  # ь не передаётся в ICAO.
  assert icao_9303("РЫБАЛЬЧЕНКО") == "RYBALCHENKO"


def test_icao_collapses_yo_to_e():
  # ё -> e сливается с е -> e (обратимости нет).
  assert icao_9303("ЁЛКА") == icao_9303("ЕЛКА") == "ELKA"


def test_iso_9_translates_yo_to_e_with_diaeresis():
  assert iso_9("ЁЛКА") == "ËLKA"
