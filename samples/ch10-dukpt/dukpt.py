from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# keyUsage codes из X9.24-3 sec.6.3.3
KU_INITIAL_KEY = 0x8001
KU_DERIVATION_KEY = 0x8000  # Intermediate Derivation Key (IDK)
KU_PIN_ENCRYPTION = 0x1000
KU_MAC_GENERATION = 0x2000
KU_DATA_ENCRYPTION = 0x3000

_ALG_AES128 = 0x0002
_KEY_LENGTH_AES128 = 0x0080  # 128 бит
_VERSION = 0x01
_BLOCK_COUNTER = 0x01


def make_derivation_data(key_usage: int, payload: bytes) -> bytes:
  """Собрать 16-байтовый блок derivation data по X9.24-3 sec.6.3.
  Поле payload -- либо InitialKeyID целиком (для Initial Key),
  либо последние 4 байта IKI плюс 4 байта transaction counter
  (для IDK и working keys).
  """
  assert len(payload) == 8
  return (
    bytes([_VERSION, _BLOCK_COUNTER])
    + key_usage.to_bytes(2, "big")
    + _ALG_AES128.to_bytes(2, "big")
    + _KEY_LENGTH_AES128.to_bytes(2, "big")
    + payload
  )


def aes_ecb_block(key: bytes, block: bytes) -> bytes:
  """Один блок AES-128 ECB -- единственный примитив деривации в AES DUKPT."""
  assert len(key) == 16 and len(block) == 16
  enc = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
  return enc.update(block) + enc.finalize()


def derive_initial_key(bdk: bytes, iki: bytes) -> bytes:
  """BDK + InitialKeyID -> Initial Key. Однократно при настройке терминала."""
  assert len(iki) == 8
  return aes_ecb_block(bdk, make_derivation_data(KU_INITIAL_KEY, iki))


def derive_idk(initial_key: bytes, iki: bytes, counter: int) -> bytes:
  """Initial Key + counter -> Intermediate Derivation Key для данной counter-позиции."""
  payload = iki[4:] + counter.to_bytes(4, "big")
  return aes_ecb_block(initial_key, make_derivation_data(KU_DERIVATION_KEY, payload))


def derive_working_key(idk: bytes, iki: bytes, counter: int, key_usage: int) -> bytes:
  """IDK + назначение (PIN / MAC / Data) -> одноразовый working key транзакции."""
  payload = iki[4:] + counter.to_bytes(4, "big")
  return aes_ecb_block(idk, make_derivation_data(key_usage, payload))
