import sys
from pathlib import Path

import pytest

from de55 import DE55, decode

# emv_keys.py живёт в соседнем sample-каталоге (глава про криптографию).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ch10-emv-keys"))

from emv_keys import arqc, derive_session_key, derive_udk

# EMV-деривация зовёт 3DES, библиотека помечает его устаревшим -- глушим.
pytestmark = pytest.mark.filterwarnings(
  "ignore::cryptography.utils.CryptographyDeprecationWarning"
)

# Ключи деривации -- эталонный вектор BP-Tools/UL (UDK независимо верифицирован
# в test_emv_keys.py). PAN и PSN в DE 55 не входят (едут в DE 2 / DE 23).
IMK = bytes.fromhex("9E15204313F7318ACB79B90BD986AD29")
PAN = "5413330089020011"
PSN = "03"

# Порядок данных под криптограмму (CVN 18): поля CDOL1 терминала, затем
# приложенные картой 82, 9F36, 9F10 (EMV Book 2, Annex A1.2).
CDOL1 = ["9F02", "9F03", "9F1A", "95", "5F2A", "9A", "9C", "9F37", "9F35"]
CARD = ["82", "9F36", "9F10"]


def test_de55_decodes_to_expected_tag_sequence():
  assert [tag for tag, _, _ in decode(DE55)] == [
    "82",
    "95",
    "9B",
    "9A",
    "9C",
    "9F02",
    "9F03",
    "5F2A",
    "9F1A",
    "9F37",
    "9F35",
    "9F36",
    "9F10",
    "9F26",
    "9F27",
    "9F34",
  ]


def test_tvr_matches_chapter_example():
  values = {tag: value for tag, value, _ in decode(DE55)}
  assert values["95"] == "0000080000"  # TVR = 0x0000080000 из примера главы


def test_cryptogram_is_eight_bytes_and_cid_is_arqc():
  values = {tag: value for tag, value, _ in decode(DE55)}
  assert len(bytes.fromhex(values["9F26"])) == 8
  assert values["9F27"] == "80"  # CID -- ARQC


def test_arqc_matches_emv_keys_derivation():
  """Сквозная проверка: IMK -> UDK -> сессионный ключ -> ARQC == 9F26 в DE 55."""
  values = {tag: value for tag, value, _ in decode(DE55)}
  udk = derive_udk(IMK, PAN, PSN)
  sk = derive_session_key(udk, bytes.fromhex(values["9F36"]))  # ATC из DE 55
  data = bytes.fromhex("".join(values[t] for t in CDOL1 + CARD))
  assert arqc(sk, data).hex().upper() == values["9F26"]
