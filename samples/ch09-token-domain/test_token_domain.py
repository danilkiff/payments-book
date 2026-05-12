from token_domain import Channel, Request, TokenRestrictions, check_domain

# NFC-токен мобильного кошелька: один канал, один TRID, без ограничения по MID.
WALLET_TOKEN = TokenRestrictions(
  allowed_channels=frozenset({Channel.CONTACTLESS}),
  token_requestor_id="50110030273",
  allowed_merchants=None,
)

# Токен подписки: только recurring у одного конкретного ТСП.
SUBSCRIPTION_TOKEN = TokenRestrictions(
  allowed_channels=frozenset({Channel.RECURRING}),
  token_requestor_id="50110099001",
  allowed_merchants=frozenset({"NETFLIX-001"}),
)


def test_wallet_in_contactless_channel_passes():
  req = Request(Channel.CONTACTLESS, "50110030273", "any-pos-merchant")
  assert check_domain(WALLET_TOKEN, req) is None


def test_wallet_in_cnp_is_rejected_by_channel():
  req = Request(Channel.CNP, "50110030273", "merchant-x")
  reason = check_domain(WALLET_TOKEN, req)
  assert reason is not None
  assert "канал" in reason


def test_wrong_trid_is_rejected():
  req = Request(Channel.CONTACTLESS, "OTHER-TRID", "merchant-x")
  reason = check_domain(WALLET_TOKEN, req)
  assert reason is not None
  assert "TRID" in reason


def test_subscription_at_allowed_merchant_passes():
  req = Request(Channel.RECURRING, "50110099001", "NETFLIX-001")
  assert check_domain(SUBSCRIPTION_TOKEN, req) is None


def test_subscription_at_other_merchant_is_rejected():
  req = Request(Channel.RECURRING, "50110099001", "OTHER-MERCHANT")
  reason = check_domain(SUBSCRIPTION_TOKEN, req)
  assert reason is not None
  assert "MID" in reason


def test_subscription_token_cannot_be_used_for_one_off_cnp():
  req = Request(Channel.CNP, "50110099001", "NETFLIX-001")
  reason = check_domain(SUBSCRIPTION_TOKEN, req)
  assert reason is not None
  assert "канал" in reason


def test_token_allowed_in_multiple_channels():
  multi = TokenRestrictions(
    allowed_channels=frozenset({Channel.CONTACTLESS, Channel.CNP}),
    token_requestor_id="X",
  )
  assert check_domain(multi, Request(Channel.CONTACTLESS, "X", "m")) is None
  assert check_domain(multi, Request(Channel.CNP, "X", "m")) is None
  assert check_domain(multi, Request(Channel.RECURRING, "X", "m")) is not None
