"""Тесты на официальных векторах из Supplement to ANSI X9.24-3-2017 Test Vectors,
sec. 2.2-2.3.1 (https://x9.org/wp-content/uploads/2018/03/X9.24-3-2017-Test-Vectors-20180129-1.pdf).
"""

from dukpt import (
  KU_DATA_ENCRYPTION,
  KU_MAC_GENERATION,
  KU_PIN_ENCRYPTION,
  derive_idk,
  derive_initial_key,
  derive_working_key,
  make_derivation_data,
)

BDK = bytes.fromhex("FEDCBA9876543210F1F1F1F1F1F1F1F1")
IKI = bytes.fromhex("1234567890123456")


def test_initial_key_matches_x9_vector():
  assert derive_initial_key(BDK, IKI) == bytes.fromhex(
    "1273671EA26AC29AFA4D1084127652A1"
  )


def test_idk_counter_1_matches_x9_vector():
  ik = derive_initial_key(BDK, IKI)
  assert derive_idk(ik, IKI, 1) == bytes.fromhex("4F21B565BAD9835E112B6465635EAE44")


def test_pin_encryption_key_counter_1_matches_x9_vector():
  ik = derive_initial_key(BDK, IKI)
  idk = derive_idk(ik, IKI, 1)
  pin_key = derive_working_key(idk, IKI, 1, KU_PIN_ENCRYPTION)
  assert pin_key == bytes.fromhex("AF8CB133A78F8DC2D1359F18527593FB")


def test_derivation_data_structure_initial_key():
  # version(01) | blockCnt(01) | keyUsage(8001) | algo(0002) | len(0080) | IKI(8B)
  dd = make_derivation_data(0x8001, IKI)
  assert dd.hex().upper() == "01018001000200801234567890123456"


def test_derivation_data_structure_pin_with_counter():
  # payload для working key: последние 4 байта IKI + 4 байта counter
  payload = IKI[4:] + (1).to_bytes(4, "big")
  dd = make_derivation_data(0x1000, payload)
  assert dd.hex().upper() == "01011000000200809012345600000001"


def test_different_usages_yield_different_keys():
  """keyUsage в derivation data меняет результат -- это и есть key separation."""
  ik = derive_initial_key(BDK, IKI)
  idk = derive_idk(ik, IKI, 1)
  pin = derive_working_key(idk, IKI, 1, KU_PIN_ENCRYPTION)
  mac = derive_working_key(idk, IKI, 1, KU_MAC_GENERATION)
  data = derive_working_key(idk, IKI, 1, KU_DATA_ENCRYPTION)
  assert len({pin, mac, data}) == 3


def test_different_counters_yield_different_pin_keys():
  """Forward secrecy опирается на то, что разные counter дают разные ключи."""
  ik = derive_initial_key(BDK, IKI)
  pin_1 = derive_working_key(derive_idk(ik, IKI, 1), IKI, 1, KU_PIN_ENCRYPTION)
  pin_2 = derive_working_key(derive_idk(ik, IKI, 2), IKI, 2, KU_PIN_ENCRYPTION)
  assert pin_1 != pin_2
