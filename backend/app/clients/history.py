"""Cálculo del historial del cliente — fuente de verdad ÚNICA (UI + LLM).

El historial mostrado se DERIVA al leer (no se guarda), así nunca se desincroniza:
crear o analizar un claim ya cambia lo que devuelve el próximo GET.

    historial = baseline sembrado (columnas del Client, congeladas) + derivado de los claims

Decisiones de producto:
- Aditivo: current = baseline + claims reales del sistema.
- Un claim SIN analizar (justificación vacía = recién creado) cuenta solo en past_claim_count
  (y en los últimos 90 días si es reciente), NO en los buckets de resultado.
- last_90_days_claim_count se deriva 100% de created_at (ventana móvil; el baseline
  congelado no aplica).
- Bucket: manual_review_required gana siempre; si no, supported->aceptado,
  contradicted->rechazado, not_enough_information->revisión manual.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.claims.models import ClaimCase
from app.clients.models import Client
from app.clients.schemas import ClientHistory


def _recent(claim: ClaimCase, cutoff: datetime) -> bool:
    ts = claim.created_at
    if ts is None:
        return False
    if ts.tzinfo is None:                      # tolera timestamps naive (p. ej. SQLite)
        ts = ts.replace(tzinfo=timezone.utc)
    return ts >= cutoff


def _is_analyzed(claim: ClaimCase) -> bool:
    """Un claim se considera analizado por IA si tiene justificación (vacía = recién creado)."""
    return bool((claim.claim_status_justification or "").strip())


def _bucket(claim: ClaimCase) -> str:
    """Clasifica un claim ANALIZADO en un bucket de resultado."""
    if "manual_review_required" in (claim.risk_flags or []):
        return "manual_review"
    if claim.claim_status == "supported":
        return "accept"
    if claim.claim_status == "contradicted":
        return "rejected"
    return "manual_review"   # not_enough_information


def _summary(past: int, accept: int, manual: int, rejected: int,
             baseline_summary: str | None) -> str:
    pending = past - accept - manual - rejected
    detail = []
    if accept:
        detail.append(f"{accept} aceptados")
    if rejected:
        detail.append(f"{rejected} rechazados")
    if manual:
        detail.append(f"{manual} en revisión")
    if pending > 0:
        detail.append(f"{pending} pendientes")
    counts = f"{past} reclamos" + (": " + ", ".join(detail) if detail else "")
    if baseline_summary and baseline_summary.strip():
        return f"{counts}. {baseline_summary.strip()}"
    return counts + "."


def compute_client_history(db: Session, client: Client, exclude_id: int | None = None) -> ClientHistory:
    """Historial efectivo del cliente: baseline (columnas sembradas) + derivado de claims.

    `exclude_id`: el LLM excluye el claim que está analizando (no debe verse a sí mismo en
    su propio historial); la UI no pasa exclude_id.
    """
    query = db.query(ClaimCase).filter(ClaimCase.user_id == client.user_id)
    if exclude_id is not None:
        query = query.filter(ClaimCase.id != exclude_id)
    claims = query.all()

    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    d_accept = d_manual = d_rejected = d_last90 = 0
    derived_flags: set[str] = set()
    for c in claims:
        if _recent(c, cutoff):
            d_last90 += 1
        if _is_analyzed(c):
            bucket = _bucket(c)
            if bucket == "accept":
                d_accept += 1
            elif bucket == "rejected":
                d_rejected += 1
            else:
                d_manual += 1
        if "manual_review_required" in (c.risk_flags or []):
            derived_flags.add("manual_review_required")

    past = (client.past_claim_count or 0) + len(claims)
    accept = (client.accept_claim or 0) + d_accept
    manual = (client.manual_review_claim or 0) + d_manual
    rejected = (client.rejected_claim or 0) + d_rejected
    last90 = d_last90   # ventana móvil: solo derivado, sin baseline

    flags = [f for f in (client.history_flags or []) if f != "none"]
    for f in sorted(derived_flags):
        if f not in flags:
            flags.append(f)
    if rejected >= 2 and "user_history_risk" not in flags:
        flags.insert(0, "user_history_risk")

    return ClientHistory(
        past_claim_count=past,
        accept_claim=accept,
        manual_review_claim=manual,
        rejected_claim=rejected,
        last_90_days_claim_count=last90,
        history_flags=flags,
        history_summary=_summary(past, accept, manual, rejected, client.history_summary),
    )
