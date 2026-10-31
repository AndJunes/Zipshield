"""Client history computation — the SINGLE source of truth (UI + LLM).

The displayed history is DERIVED on read (never stored), so it can never drift:
creating or analyzing a claim already changes what the next GET returns.

    history = seeded baseline (frozen Client columns) + derived from the claims

Product decisions:
- Additive: current = baseline + the system's real claims.
- An UNANALYZED claim (empty justification = just created) only counts in past_claim_count
  (and in the last 90 days if recent), NOT in the outcome buckets.
- last_90_days_claim_count is derived 100% from created_at (rolling window; the frozen
  baseline does not apply).
- Bucket: manual_review_required always wins; otherwise supported->accepted,
  contradicted->rejected, not_enough_information->manual review.
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
    if ts.tzinfo is None:                      # tolerate naive timestamps (e.g. SQLite)
        ts = ts.replace(tzinfo=timezone.utc)
    return ts >= cutoff


def _is_analyzed(claim: ClaimCase) -> bool:
    """A claim counts as analyzed if it has a justification (empty = just created)."""
    return bool((claim.claim_status_justification or "").strip())


def _bucket(claim: ClaimCase) -> str:
    """Classify an ANALYZED claim into an outcome bucket."""
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


def compute_client_history(
    db: Session, client: Client, exclude_id: int | None = None,
    claims: list[ClaimCase] | None = None,
) -> ClientHistory:
    """Effective client history: baseline (seeded columns) + derived from claims.

    `exclude_id`: the LLM excludes the claim it is analyzing (it must not see itself in
    its own history); the UI does not pass exclude_id.

    `claims`: if the caller already fetched this client's claims (e.g. a listing that
    loaded them all at once to avoid N+1), they are reused as-is instead of being
    re-queried here per client.
    """
    if claims is None:
        query = db.query(ClaimCase).filter(ClaimCase.user_id == client.user_id)
        if exclude_id is not None:
            query = query.filter(ClaimCase.id != exclude_id)
        claims = query.all()
    elif exclude_id is not None:
        claims = [c for c in claims if c.id != exclude_id]

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
    last90 = d_last90   # rolling window: derived only, no baseline

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
