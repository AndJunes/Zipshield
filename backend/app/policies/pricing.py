"""Motor de tarificación (rating) simple pero realista.

La prima NO se escribe a mano: se calcula a partir de la suma asegurada, un catálogo de
coberturas por producto (cada una con su tasa, deducible y límite) y factores de riesgo.
Modelo multiplicativo (estándar en seguros). Devuelve un desglose auditable.

    prima_cobertura = suma_asegurada × tasa × risk_factor × factor_deducible
    net_premium     = max(min_premium, Σ primas_coberturas)
    total           = net_premium + policy_fee + net_premium × tax_rate
"""

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


def _deductible_factor(deductible: float, sum_insured: float) -> float:
    """Más deducible → prima más barata (el cliente asume más riesgo)."""
    if not sum_insured:
        return 1.0
    ratio = float(deductible) / float(sum_insured)
    return round(1.0 - min(0.30, ratio), 4)


def quote(policy_type: str, sum_insured, risk_factor: float = 1.0) -> dict:
    """Cotiza una póliza. Devuelve un desglose con las coberturas y los montos."""
    cfg = RATE_TABLE.get(policy_type)
    cov_defs = COVERAGE_CATALOG.get(policy_type, [])
    if cfg is None:
        raise ValueError(f"Producto desconocido: {policy_type}")

    si = float(sum_insured)
    coverages = []
    net = 0.0
    for c in cov_defs:
        factor_ded = _deductible_factor(c["deductible"], si)
        premium = round(si * c["rate"] * risk_factor * factor_ded, 2)
        coverages.append({
            "code": c["code"],
            "name": c["name"],
            "limit_amount": round(si * c["limit_factor"], 2),
            "deductible": float(c["deductible"]),
            "premium": premium,
        })
        net += premium

    net_premium = round(max(net, cfg["min_premium"]), 2)
    taxes_fees = round(cfg["policy_fee"] + net_premium * cfg["tax_rate"], 2)
    total = round(net_premium + taxes_fees, 2)
    base_rate = round(net_premium / si, 4) if si else 0.0

    return {
        "coverages": coverages,
        "net_premium": net_premium,
        "taxes_fees": taxes_fees,
        "total_premium": total,
        "base_rate": base_rate,
        "policy_fee": cfg["policy_fee"],
        "tax_rate": cfg["tax_rate"],
        "risk_factor": risk_factor,
    }
