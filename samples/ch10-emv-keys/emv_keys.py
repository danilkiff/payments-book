from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_COMPLEMENT = b"\xff" * 8  # маска XOR для правой половины UDK (Option A)


def des3_ecb_block(key: bytes, block: bytes) -> bytes:
  """Один блок 3DES (TDEA) в~ECB -- единственный примитив деривации EMV.
  Ключ 16 байт (double-length), блок 8 байт."""
  assert len(key) == 16 and len(block) == 8
  enc = Cipher(algorithms.TripleDES(key), modes.ECB()).encryptor()
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
  y = bytes.fromhex(digits)                  # 8 байт BCD
  left = des3_ecb_block(imk, y)
  right = des3_ecb_block(imk, bytes(a ^ b for a, b in zip(y, _COMPLEMENT)))
  return adjust_parity(left + right)


def derive_session_key(udk: bytes, atc: bytes) -> bytes:
  """UDK + ATC -> сессионный ключ SK (EMV Common Session Key, Book 2, A1.3).
  Левая половина ветвится байтом 'F0', правая -- '0F'; остальные байты нулевые."""
  assert len(atc) == 2
  left = des3_ecb_block(udk, atc + b"\xf0" + b"\x00" * 5)
  right = des3_ecb_block(udk, atc + b"\x0f" + b"\x00" * 5)
  return adjust_parity(left + right)
