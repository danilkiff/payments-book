from translit import bgn_pcgn, icao_9303, iso_9


def test_iso_9_keeps_one_to_one_with_diacritics():
  assert iso_9("ЦАРЁВ") == "CARËV"
  assert iso_9("ЩУКИН") == "ŜUKIN"
  assert iso_9("ЖЁЛТЫЙ") == "ŽËLTYJ"


def test_icao_9303_keeps_ascii_only():
  assert icao_9303("ЦАРЁВ") == "TSAREV"
  assert icao_9303("ЩУКИН") == "SHCHUKIN"
  assert icao_9303("ФЁДОРОВ") == "FEDOROV"
  # ь не передаётся
  assert icao_9303("РЫБАЛЬЧЕНКО") == "RYBALCHENKO"


def test_bgn_pcgn_uses_ye_at_word_start():
  assert bgn_pcgn("Елкин") == "Yelkin"
  assert bgn_pcgn("Ёлкин") == "Yëlkin"


def test_bgn_pcgn_keeps_e_after_consonant():
  # После согласной "р" в Царёв буква ё романизируется как ë, не как yë.
  assert bgn_pcgn("Царёв") == "Tsarëv"
  # После согласной в Федоров е остаётся e, не ye.
  assert bgn_pcgn("Федоров") == "Fedorov"


def test_bgn_pcgn_uses_ye_after_vowel():
  # После согласной в "Кузнецов" е остаётся e.
  assert bgn_pcgn("Кузнецов") == "Kuznetsov"
  # После гласной в "Заев" -- ye.
  assert bgn_pcgn("Заев") == "Zayev"


def test_evgeniy_three_systems():
  # Классический пример карточной транслитерации:
  # один банк пишет EVGENIY (BGN/PCGN), другой -- EVGENII (ICAO),
  # третий по советским правилам -- EVGENIJ (ISO 9).
  assert bgn_pcgn("ЕВГЕНИЙ") == "YEVGENIY"
  assert icao_9303("ЕВГЕНИЙ") == "EVGENII"
  assert iso_9("ЕВГЕНИЙ") == "EVGENIJ"


def test_ekaterina_three_systems():
  assert bgn_pcgn("ЕКАТЕРИНА") == "YEKATERINA"
  assert icao_9303("ЕКАТЕРИНА") == "EKATERINA"
  assert iso_9("ЕКАТЕРИНА") == "EKATERINA"


def test_yuriy_three_systems():
  # Юрий: ю + й -- расхождение по всем трём стандартам.
  assert bgn_pcgn("ЮРИЙ") == "YURIY"
  assert icao_9303("ЮРИЙ") == "IURII"
  assert iso_9("ЮРИЙ") == "ÛRIJ"


def test_three_systems_diverge_on_softsign_and_yo():
  assert iso_9("СОЛЬЁВ") == "SOLʹËV"
  assert bgn_pcgn("Сольёв") == "Solʹyëv"
  assert icao_9303("СОЛЬЁВ") == "SOLEV"


def test_iso_9_roundtrip_simple_cases():
  assert iso_9("ИВАНОВ") == "IVANOV"
  assert iso_9("ЁЛКА") == "ËLKA"


def test_full_name_preserves_word_boundaries_and_case():
  # Имя-Отчество-Фамилия с разными правилами на каждом слове.
  src = "Юрий Евгеньевич Иванов"
  assert bgn_pcgn(src) == "Yuriy Yevgenʹyevich Ivanov"
  assert icao_9303(src) == "Iurii Evgenevich Ivanov"
