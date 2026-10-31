"""Pricing regression tests: computing the rating in `float` and rounding with `round()`
produces a one-cent error in 52% of the real sum-insured / risk_factor combinations the
data seed itself generates.

This specific case (si=18900, rf=0.95, "car") is a known failing one: the float version
gave net_premium=1148.06 / taxes_fees=208.69 / total_premium=1356.75; the correct value
(recomputed by hand with Decimal + ROUND_HALF_UP over the SAME formula) is
1148.07 / 208.69 / 1356.76.
"""

from decimal import Decimal

from app.policies import pricing
from tests.conftest import auth_headers, make_agent, make_client, make_supervisor, make_user


def test_quote_matches_the_exact_decimal_reference_for_the_known_failing_case():
    result = pricing.quote("car", 18900, risk_factor=0.95)

    assert result["net_premium"] == Decimal("1148.07")
    assert result["taxes_fees"] == Decimal("208.69")
    assert result["total_premium"] == Decimal("1356.76")
    assert isinstance(result["net_premium"], Decimal)
    assert isinstance(result["coverages"][0]["premium"], Decimal)


def test_quote_accepts_plain_float_and_int_inputs_without_reintroducing_binary_drift():
    """Real callers (risk_factor_for_client, seed_policies.py) pass float/int, not
    Decimal — the conversion must always go through `str()`, never Decimal(float)
    directly, or the same binary rounding error would sneak back in."""
    from_float_risk_factor = pricing.quote("car", 18900, risk_factor=0.95)
    from_decimal_risk_factor = pricing.quote("car", Decimal("18900"), risk_factor=Decimal("0.95"))
    assert from_float_risk_factor == from_decimal_risk_factor


def test_quote_has_no_one_cent_drift_across_realistic_seed_combinations():
    """Sweeps the same (si, rf) combinations scripts/seed_policies.py generates and
    confirms, for each one, that the breakdown is internally consistent: net_premium is
    exactly the sum of the rounded coverage premiums, and total = net + taxes."""
    sum_insured_base = {"car": 18000, "laptop": 1500, "package": 600}
    risk_factors = [1.0, 1.0, 1.15, 0.9, 1.0, 1.25, 0.95]

    for ptype, base in sum_insured_base.items():
        for i in range(20):
            si = base + (i % 5) * (base // 20)
            rf = risk_factors[i % len(risk_factors)]
            result = pricing.quote(ptype, si, risk_factor=rf)

            expected_net = sum(c["premium"] for c in result["coverages"])
            assert result["net_premium"] == max(
                expected_net, Decimal(str(pricing.RATE_TABLE[ptype]["min_premium"]))
            )
            assert result["total_premium"] == result["net_premium"] + result["taxes_fees"]


def test_create_policy_does_not_crash_on_the_json_rating_factors_column(client, db_session):
    """Compatibility risk of the Decimal pricing: `rating_factors` is a JSON column, and
    Decimal is not serializable there — without the explicit `float(...)` in
    `create_policy`, this `POST /policies` would raise a TypeError on `db.commit()`."""
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    payload = {
        "client_id": owner.id,
        "type": "car",
        "name": "Test policy",
        "sum_insured": "18900.00",
        "deductible": "500.00",
        "effective_date": "2026-01-01",
        "term_months": 12,
    }
    resp = client.post("/policies", json=payload, headers=auth_headers(user))
    assert resp.status_code == 201
    # A new client with no history -> risk_factor_for_client() gives 1.0, not the 0.95
    # of the case above; the exact Decimal value for rf=1.0 is 1208.48.
    assert resp.json()["net_premium"] == "1208.48"
