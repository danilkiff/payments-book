from aml_classifier import Client, Decision, Kind, Operation, Verdict, classify

SANCTIONED = frozenset({"ext-001"})


def make(**kw) -> Operation:
  client_id = kw.pop("client_id", "c-1")
  client_risk = kw.pop("client_risk", "low")
  defaults: dict = {
    "amount_kopecks": 100,
    "kind": Kind.WIRE_TRANSFER,
    "client": Client(id=client_id, risk=client_risk),
    "counterparty_id": None,
  }
  defaults.update(kw)
  return Operation(**defaults)


def test_below_threshold_goes_to_normal_flow():
  op = make(amount_kopecks=999_999_99, kind=Kind.CASH_DEPOSIT)
  assert classify(op, SANCTIONED) == Verdict(Decision.NORMAL, "below_threshold")


def test_cash_deposit_at_threshold_is_mandatory():
  op = make(amount_kopecks=1_000_000_00, kind=Kind.CASH_DEPOSIT)
  v = classify(op, SANCTIONED)
  assert v.decision is Decision.MANDATORY
  assert v.reason == "threshold:cash_deposit"


def test_real_estate_uses_5m_threshold():
  below = classify(make(amount_kopecks=1_000_000_00, kind=Kind.REAL_ESTATE), SANCTIONED)
  assert below.decision is Decision.NORMAL
  at = classify(make(amount_kopecks=5_000_000_00, kind=Kind.REAL_ESTATE), SANCTIONED)
  assert at.decision is Decision.MANDATORY


def test_postal_uses_100k_threshold():
  v = classify(make(amount_kopecks=100_000_00, kind=Kind.POSTAL), SANCTIONED)
  assert v.decision is Decision.MANDATORY
  assert v.reason == "threshold:postal"


def test_gov_order_uses_600k_threshold():
  v = classify(make(amount_kopecks=600_000_00, kind=Kind.GOV_ORDER), SANCTIONED)
  assert v.decision is Decision.MANDATORY


def test_party_in_sanctioned_list_is_mandatory_at_any_amount():
  op = make(amount_kopecks=100, kind=Kind.WIRE_TRANSFER, counterparty_id="ext-001")
  v = classify(op, SANCTIONED)
  assert v.decision is Decision.MANDATORY
  assert v.reason == "party_in_list"


def test_sanctioned_client_id_also_triggers_mandatory():
  op = make(amount_kopecks=100, client_id="ext-001")
  v = classify(op, SANCTIONED)
  assert v.decision is Decision.MANDATORY


def test_high_risk_client_below_threshold_is_suspicious():
  # 600 тыс. руб. по обычному переводу: формально ниже порога 1 млн,
  # но для high-risk клиента RBA опускает планку до 500 тыс.
  op = make(amount_kopecks=600_000_00, kind=Kind.WIRE_TRANSFER, client_risk="high")
  v = classify(op, SANCTIONED)
  assert v.decision is Decision.SUSPICIOUS
  assert v.reason == "rba:high_risk_client"


def test_low_risk_client_below_threshold_is_normal():
  op = make(amount_kopecks=600_000_00, kind=Kind.WIRE_TRANSFER, client_risk="low")
  assert classify(op, SANCTIONED).decision is Decision.NORMAL


def test_wire_transfer_kind_not_in_mandatory_list_even_above_threshold():
  # WIRE_TRANSFER не входит в _KINDS_WITH_MANDATORY: ст. 6 не требует
  # обязательного контроля по сумме для обычных безналичных переводов.
  op = make(amount_kopecks=2_000_000_00, kind=Kind.WIRE_TRANSFER, client_risk="low")
  assert classify(op, SANCTIONED).decision is Decision.NORMAL
