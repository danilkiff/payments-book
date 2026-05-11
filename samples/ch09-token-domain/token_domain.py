"""Token Domain Restriction Controls: проверка применимости токена.

TSP сопоставляет канал запроса, TRID запросчика и MID ТСП с атрибутами
ограничений, записанными при выпуске токена. При несовпадении -- отказ
до того, как запрос дойдёт до эмитента (EMVCo Payment Tokenisation
Specification, ch09 \"Анатомия сетевого токена\").

Минимальный матчер. Реальные TSP (VTS, MDES, TSP НСПК) проверяют
шире: assurance method, expiry, cryptogram, статус токена.
"""

from dataclasses import dataclass
from enum import Enum


class Channel(Enum):
    CONTACTLESS = "contactless"
    CNP = "cnp"  # card-not-present, e-commerce
    RECURRING = "recurring"


@dataclass(frozen=True)
class TokenRestrictions:
    """Атрибуты, записанные TSP при выпуске токена."""

    allowed_channels: frozenset[Channel]
    token_requestor_id: str
    # None -- ограничение по MID не задано (типично для NFC-токена устройства).
    allowed_merchants: frozenset[str] | None = None


@dataclass(frozen=True)
class Request:
    channel: Channel
    token_requestor_id: str
    merchant_id: str


def check_domain(token: TokenRestrictions, request: Request) -> str | None:
    """None -- проверка пройдена; строка с причиной -- отказ."""
    if request.channel not in token.allowed_channels:
        return f"канал {request.channel.value} не входит в разрешённые"
    if request.token_requestor_id != token.token_requestor_id:
        return "TRID запроса не совпадает с TRID токена"
    if (
        token.allowed_merchants is not None
        and request.merchant_id not in token.allowed_merchants
    ):
        return f"MID {request.merchant_id} не входит в разрешённые"
    return None
