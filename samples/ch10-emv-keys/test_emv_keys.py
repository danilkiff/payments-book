"""Тесты деривации ключей EMV на независимых эталонных векторах.

UDK (Option A): вектор, на котором сошлись два независимых инструмента --
BP-Tools Cryptographic Calculator и UL Testing Tools
(https://stackoverflow.com/questions/66557301).

CSK (Common Session Key, EMV Book 2, A1.3.1): пример из спецификации приведён
ДО коррекции чётности; EMV требует нечётную чётность DES, поэтому итог сверяется
как adjust_parity(опубликованное значение) -- и совпадает с BP-Tools / EFTLab.
"""

import pytest

from emv_keys import adjust_parity, arqc, derive_session_key, derive_udk

# EMV использует double-length (16-байт) 3DES -- библиотека зовёт его устаревшим,
# но для EMV это штатный размер ключа; глушим ожидаемое предупреждение.
pytestmark = pytest.mark.filterwarnings(
  "ignore::cryptography.utils.CryptographyDeprecationWarning"
)

# --- UDK Option A: BP-Tools и UL Testing Tools дают одинаковый результат ---
IMK = bytes.fromhex("9E15204313F7318ACB79B90BD986AD29")
PAN = "5413330089020011"
PSN = "03"
UDK_EXPECTED = bytes.fromhex("4519028F544CAD6DCEE9A7C7C17562FD")

# --- CSK: пример EMV Book 2, A1.3.1 (MK, ATC=0001) ---
SK_MK = bytes.fromhex("CB45F993BDDA763EF030AF6CE1762735")
SK_ATC = bytes.fromhex("0001")
SK_PUBLISHED_PRE_PARITY = bytes.fromhex("E011BB83D8A60BEE3CDE768F68560BD9")


def test_udk_option_a_matches_external_tools():
  assert derive_udk(IMK, PAN, PSN) == UDK_EXPECTED


def test_session_key_matches_emv_book2_example():
  # Спека печатает значение до коррекции; EMV применяет нечётную чётность DES.
  assert derive_session_key(SK_MK, SK_ATC) == adjust_parity(SK_PUBLISHED_PRE_PARITY)


def test_udk_is_16_bytes_odd_parity():
  udk = derive_udk(IMK, PAN, PSN)
  assert len(udk) == 16
  assert all(bin(b).count("1") % 2 == 1 for b in udk)


def test_session_key_is_16_bytes_odd_parity():
  sk = derive_session_key(UDK_EXPECTED, SK_ATC)
  assert len(sk) == 16
  assert all(bin(b).count("1") % 2 == 1 for b in sk)


def test_session_key_unique_per_atc():
  """Уникальный ATC даёт уникальный сессионный ключ -- основа защиты от replay."""
  sk1 = derive_session_key(UDK_EXPECTED, bytes.fromhex("0001"))
  sk2 = derive_session_key(UDK_EXPECTED, bytes.fromhex("0002"))
  assert sk1 != sk2


def test_udk_depends_on_pan_sequence_number():
  """Разный PSN при том же PAN даёт разные ключи карт."""
  assert derive_udk(IMK, PAN, "03") != derive_udk(IMK, PAN, "04")


# --- Retail MAC (ISO 9797-1, алгоритм 3): независимый известный вектор ---
MAC_KEY = bytes.fromhex("7962D9ECE03D1ACD4C76089DCE131543")
MAC_MSG = bytes.fromhex(
  "72C29C2371CC9BDB65B779B8E8D37B29ECC154AA56A8799FAE2F498F76ED92F2"
)
MAC_EXPECTED = bytes.fromhex("5F1448EEA8AD90A7")


def test_retail_mac_matches_iso9797_vector():
  # Сообщение кратно 8 байтам -> padding method 2 добавляет полный блок 0x80…00.
  assert arqc(MAC_KEY, MAC_MSG) == MAC_EXPECTED
