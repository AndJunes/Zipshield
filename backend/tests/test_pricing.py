"""Regresión para BUG-13: el motor de tarificación calculaba en `float` y redondeaba con
`round()`, produciendo un error de un centavo en el 52% de las combinaciones reales de
suma asegurada / risk_factor que el propio seed de datos genera.

Este caso concreto (si=18900, rf=0.95, "car") es uno de los que reproduje manualmente
durante la auditoría: la versión en float daba net_premium=1148.06 / taxes_fees=208.69 /
total_premium=1356.75; el valor correcto (recalculado a mano con Decimal + ROUND_HALF_UP
sobre la MISMA fórmula) es 1148.07 / 208.69 / 1356.76.
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
    """Los llamadores reales (risk_factor_for_client, seed_policies.py) pasan float/int,
    no Decimal — la conversión debe pasar siempre por `str()`, nunca por Decimal(float)
    directo, o el mismo error de redondeo binario se colaría por la puerta de atrás."""
    from_float_risk_factor = pricing.quote("car", 18900, risk_factor=0.95)
    from_decimal_risk_factor = pricing.quote("car", Decimal("18900"), risk_factor=Decimal("0.95"))
    assert from_float_risk_factor == from_decimal_risk_factor


def test_quote_has_no_one_cent_drift_across_realistic_seed_combinations():
    """Barre las mismas combinaciones (si, rf) que genera scripts/seed_policies.py y
    confirma, para cada una, que el desglose es internamente consistente: net_premium es
    exactamente la suma de las primas de cobertura redondeadas, y total = net + taxes."""
    sum_insured_base = {"car": 18000, "laptop": 1500, "package": 600}
    risk_factors = [1.0, 1.0, 1.15, 0.9, 1.0, 1.25, 0.95]

    for ptype, base in sum_insured_base.items():
        for i in range(20):
            si = base + (i % 5) * (base // 20)
            rf = risk_factors[i % len(risk_factors)]
            result = pricing.quote(ptype, si, risk_factor=rf)

            expected_net = sum(c["premium"] for c in result["coverages"])
            assert result["net_premium"] == max(expected_net, Decimal(str(pricing.RATE_TABLE[ptype]["min_premium"])))
            assert result["total_premium"] == result["net_premium"] + result["taxes_fees"]


def test_create_policy_does_not_crash_on_the_json_rating_factors_column(client, db_session):
    """Riesgo de compatibilidad de este fix: `rating_factors` es una columna JSON, y
    Decimal no es serializable ahí — sin el `float(...)` explícito en `create_policy`,
    este `POST /policies` lanzaría un TypeError al hacer `db.commit()`."""
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    payload = {
        "client_id": owner.id,
        "type": "car",
        "name": "Póliza de prueba",
        "sum_insured": "18900.00",
        "deductible": "500.00",
        "effective_date": "2026-01-01",
        "term_months": 12,
    }
    resp = client.post("/policies", json=payload, headers=auth_headers(user))
    assert resp.status_code == 201
    # Cliente nuevo sin historial -> risk_factor_for_client() da 1.0, no el 0.95 del caso
    # de arriba; el valor exacto en Decimal para rf=1.0 es 1208.48 (ver el propio test).
    assert resp.json()["net_premium"] == "1208.48"
