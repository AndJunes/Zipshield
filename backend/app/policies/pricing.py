"""Motor de tarificación (rating) simple pero realista.

La prima NO se escribe a mano: se calcula a partir de la suma asegurada, un catálogo de
coberturas por producto (cada una con su tasa, deducible y límite) y factores de riesgo.
Modelo multiplicativo (estándar en seguros). Devuelve un desglose auditable.

    prima_cobertura = suma_asegurada × tasa × risk_factor × factor_deducible
    net_premium     = max(min_premium, Σ primas_coberturas)
    total           = net_premium + policy_fee + net_premium × tax_rate

Todo el cálculo se hace en `Decimal` (ver BUG-13 en QA_AUDIT_REPORT.md): computar dinero en
`float` produce errores de redondeo de un centavo en más de la mitad de las combinaciones
reales de suma asegurada/risk_factor que genera el propio seed de datos.
"""

from decimal import Decimal, ROUND_HALF_UP

_TWO_PLACES = Decimal("0.01")
_FOUR_PLACES = Decimal("0.0001")


def _to_decimal(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _q2(value: Decimal) -> Decimal:
    return value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

# Parámetros por producto (Line of Business). Como el reference.py del LLM: data, no DDL.
RATE_TABLE = {
    "car":     {"min_premium": 200, "policy_fee": 25, "tax_rate": 0.16},
    "laptop":  {"min_premium": 50,  "policy_fee": 10, "tax_rate": 0.16},
    "package": {"min_premium": 120, "policy_fee": 15, "tax_rate": 0.16},
}

# Catálogo de coberturas válidas por producto (conecta car/laptop/package de Zipshield
# con coberturas reales de P&C / inland marine).
COVERAGE_CATALOG = {
    "car": [
        {"code": "collision",       "name": "Colisión",              "rate": 0.030, "deductible": 500, "limit_factor": 1.0},
        {"code": "comprehensive",   "name": "Cobertura amplia",      "rate": 0.020, "deductible": 250, "limit_factor": 1.0},
        {"code": "liability_bi_pd", "name": "Responsabilidad civil", "rate": 0.015, "deductible": 0,   "limit_factor": 2.0},
    ],
    "laptop": [
        {"code": "accidental_damage", "name": "Daño accidental",   "rate": 0.060, "deductible": 50,  "limit_factor": 1.0},
        {"code": "liquid_damage",     "name": "Daño por líquidos", "rate": 0.030, "deductible": 100, "limit_factor": 1.0},
        {"code": "theft",             "name": "Robo",              "rate": 0.025, "deductible": 50,  "limit_factor": 1.0},
    ],
    "package": [
        {"code": "transit_damage", "name": "Daño en tránsito", "rate": 0.040, "deductible": 0, "limit_factor": 1.0},
        {"code": "loss_theft",     "name": "Pérdida o robo",   "rate": 0.030, "deductible": 0, "limit_factor": 1.0},
    ],
}


def _deductible_factor(deductible, sum_insured: Decimal) -> Decimal:
    """Más deducible → prima más barata (el cliente asume más riesgo)."""
    if not sum_insured:
        return Decimal("1")
    ratio = _to_decimal(deductible) / sum_insured
    return (Decimal("1") - min(Decimal("0.30"), ratio)).quantize(_FOUR_PLACES, rounding=ROUND_HALF_UP)


def quote(policy_type: str, sum_insured, risk_factor=Decimal("1.0")) -> dict:
    """Cotiza una póliza. Devuelve un desglose con las coberturas y los montos."""
    cfg = RATE_TABLE.get(policy_type)
    cov_defs = COVERAGE_CATALOG.get(policy_type, [])
    if cfg is None:
        raise ValueError(f"Producto desconocido: {policy_type}")

    si = _to_decimal(sum_insured)
    rf = _to_decimal(risk_factor)
    coverages = []
    net = Decimal("0")
    for c in cov_defs:
        rate = _to_decimal(c["rate"])
        factor_ded = _deductible_factor(c["deductible"], si)
        premium = _q2(si * rate * rf * factor_ded)
        coverages.append({
            "code": c["code"],
            "name": c["name"],
            "limit_amount": _q2(si * _to_decimal(c["limit_factor"])),
            "deductible": _to_decimal(c["deductible"]),
            "premium": premium,
        })
        net += premium

    net_premium = _q2(max(net, _to_decimal(cfg["min_premium"])))
    taxes_fees = _q2(_to_decimal(cfg["policy_fee"]) + net_premium * _to_decimal(cfg["tax_rate"]))
    total = _q2(net_premium + taxes_fees)
    base_rate = (net_premium / si).quantize(_FOUR_PLACES, rounding=ROUND_HALF_UP) if si else Decimal("0")

    return {
        "coverages": coverages,
        "net_premium": net_premium,
        "taxes_fees": taxes_fees,
        "total_premium": total,
        "base_rate": base_rate,
        "policy_fee": cfg["policy_fee"],
        "tax_rate": cfg["tax_rate"],
        "risk_factor": rf,
    }
