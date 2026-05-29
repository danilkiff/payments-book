from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
from cryptography.hazmat.primitives.ciphers import Cipher, modes

_COMPLEMENT = b"\xff" * 8  # маска XOR для правой половины UDK (Option A)


def des3_ecb_block(key: bytes, block: bytes) -> bytes:
  """Один блок 3DES (TDEA) в ECB -- единственный примитив деривации EMV.
  Ключ 16 байт (double-length), блок 8 байт."""
  assert len(key) == 16 and len(block) == 8
  enc = Cipher(TripleDES(key), modes.ECB()).encryptor()
  return enc.update(block) + enc.finalize()


def adjust_parity(key: bytes) -> bytes:
  """Нечётная чётность DES: младший бит каждого байта -- бит чётности."""
  out = bytearray(key)
  for i, b in enumerate(out):
    if bin(b).count("1") % 2 == 0:
      out[i] = b ^ 1
  return bytes(out)


def derive_udk(imk: bytes, pan: str, psn: str = "00") -> bytes:
  """IMK + PAN + PAN Sequence Number -> ключ карты UDK.
  EMV Book 2, Annex A1.4, Option A (PAN до 16 цифр). Для длинных PAN --
  Option B: Y получается децимализацией SHA-1 от PAN||PSN, далее без изменений."""
  digits = (pan + psn)[-16:].rjust(16, "0")  # 16 младших цифр, дополнение слева
  y = bytes.fromhex(digits)  # 8 байт BCD
  left = des3_ecb_block(imk, y)
  right = des3_ecb_block(imk, bytes(a ^ b for a, b in zip(y, _COMPLEMENT, strict=True)))
  return adjust_parity(left + right)


def derive_session_key(udk: bytes, atc: bytes) -> bytes:
  """UDK + ATC -> сессионный ключ SK (EMV Common Session Key, Book 2, A1.3).
  Левая половина ветвится байтом 'F0', правая -- '0F'; остальные байты нулевые."""
  assert len(atc) == 2
  left = des3_ecb_block(udk, atc + b"\xf0" + b"\x00" * 5)
  right = des3_ecb_block(udk, atc + b"\x0f" + b"\x00" * 5)
  return adjust_parity(left + right)


def _des_ecb_block(key: bytes, block: bytes) -> bytes:
  """Один блок одинарного DES в ECB (ключ 8 байт)."""
  assert len(key) == 8 and len(block) == 8
  enc = Cipher(TripleDES(key), modes.ECB()).encryptor()
  return enc.update(block) + enc.finalize()


def _pad_method2(data: bytes) -> bytes:
  """ISO/IEC 9797-1 padding method 2: добавить 0x80, затем 0x00 до кратности 8."""
  data += b"\x80"
  while len(data) % 8:
    data += b"\x00"
  return data


def _xor8(a: bytes, b: bytes) -> bytes:
  return bytes(x ^ y for x, y in zip(a, b, strict=True))


def arqc(session_key: bytes, data: bytes) -> bytes:
  """Криптограмма EMV (ARQC/TC/AAC): Retail MAC по ISO/IEC 9797-1 алгоритм 3
  поверх данных транзакции на сессионном ключе (EMV Book 2, Annex A1.2).
  CBC одинарным DES на левой половине ключа, финальный блок -- 2-key 3DES."""
  assert len(session_key) == 16
  kl, kr = session_key[:8], session_key[8:]
  blocks = _pad_method2(data)
  h = bytes(8)
  for i in range(0, len(blocks) - 8, 8):
    h = _des_ecb_block(kl, _xor8(blocks[i : i + 8], h))
  return des3_ecb_block(kl + kr, _xor8(blocks[-8:], h))
