"""Simple but realistic rating engine.

The premium is NOT typed in by hand: it is computed from the sum insured, a per-product
coverage catalog (each with its own rate, deductible and limit) and risk factors.
Multiplicative model (standard in insurance). Returns an auditable breakdown.

    coverage_premium = sum_insured × rate × risk_factor × deductible_factor
    net_premium      = max(min_premium, Σ coverage_premiums)
    total            = net_premium + policy_fee + net_premium × tax_rate

All math is done in `Decimal`: computing money in `float` produces one-cent rounding
errors in more than half of the real sum-insured/risk_factor combinations the data seed
itself generates.
"""

from decimal import ROUND_HALF_UP, Decimal

_TWO_PLACES = Decimal("0.01")
_FOUR_PLACES = Decimal("0.0001")


def _to_decimal(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _q2(value: Decimal) -> Decimal:
    return value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


# Per-product (Line of Business) parameters. Like the LLM's reference.py: data, not DDL.
RATE_TABLE = {
    "car": {"min_premium": 200, "policy_fee": 25, "tax_rate": 0.16},
    "laptop": {"min_premium": 50, "policy_fee": 10, "tax_rate": 0.16},
    "package": {"min_premium": 120, "policy_fee": 15, "tax_rate": 0.16},
}

# Catalog of valid coverages per product (maps Zipshield's car/laptop/package to real
# P&C / inland marine coverages).
COVERAGE_CATALOG = {
    "car": [
        {
            "code": "collision",
            "name": "Colisión",
            "rate": 0.030,
            "deductible": 500,
            "limit_factor": 1.0,
        },
        {
            "code": "comprehensive",
            "name": "Cobertura amplia",
            "rate": 0.020,
            "deductible": 250,
            "limit_factor": 1.0,
        },
        {
            "code": "liability_bi_pd",
            "name": "Responsabilidad civil",
            "rate": 0.015,
            "deductible": 0,
            "limit_factor": 2.0,
        },
    ],
    "laptop": [
        {
            "code": "accidental_damage",
            "name": "Daño accidental",
            "rate": 0.060,
            "deductible": 50,
            "limit_factor": 1.0,
        },
        {
            "code": "liquid_damage",
            "name": "Daño por líquidos",
            "rate": 0.030,
            "deductible": 100,
            "limit_factor": 1.0,
        },
        {"code": "theft", "name": "Robo", "rate": 0.025, "deductible": 50, "limit_factor": 1.0},
    ],
    "package": [
        {
            "code": "transit_damage",
            "name": "Daño en tránsito",
            "rate": 0.040,
            "deductible": 0,
            "limit_factor": 1.0,
        },
        {
            "code": "loss_theft",
            "name": "Pérdida o robo",
            "rate": 0.030,
            "deductible": 0,
            "limit_factor": 1.0,
        },
    ],
}


def _deductible_factor(deductible, sum_insured: Decimal) -> Decimal:
    """Higher deductible → cheaper premium (the client takes on more risk)."""
    if not sum_insured:
        return Decimal("1")
    ratio = _to_decimal(deductible) / sum_insured
    return (Decimal("1") - min(Decimal("0.30"), ratio)).quantize(
        _FOUR_PLACES, rounding=ROUND_HALF_UP
    )


def quote(policy_type: str, sum_insured, risk_factor=Decimal("1.0")) -> dict:
    """Quote a policy. Returns a breakdown with the coverages and amounts."""
    cfg = RATE_TABLE.get(policy_type)
    cov_defs = COVERAGE_CATALOG.get(policy_type, [])
    if cfg is None:
        raise ValueError(f"Unknown product: {policy_type}")

    si = _to_decimal(sum_insured)
    rf = _to_decimal(risk_factor)
    coverages = []
    net = Decimal("0")
    for c in cov_defs:
        rate = _to_decimal(c["rate"])
        factor_ded = _deductible_factor(c["deductible"], si)
        premium = _q2(si * rate * rf * factor_ded)
        coverages.append(
            {
                "code": c["code"],
                "name": c["name"],
                "limit_amount": _q2(si * _to_decimal(c["limit_factor"])),
                "deductible": _to_decimal(c["deductible"]),
                "premium": premium,
            }
        )
        net += premium

    net_premium = _q2(max(net, _to_decimal(cfg["min_premium"])))
    taxes_fees = _q2(_to_decimal(cfg["policy_fee"]) + net_premium * _to_decimal(cfg["tax_rate"]))
    total = _q2(net_premium + taxes_fees)
    base_rate = (
        (net_premium / si).quantize(_FOUR_PLACES, rounding=ROUND_HALF_UP) if si else Decimal("0")
    )

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
