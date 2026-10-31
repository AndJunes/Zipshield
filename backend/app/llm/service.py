"""Orchestrates LLM analysis of a claim.

Public piece:
    analyze_claim(db, claim) -> dict with the 10 analysis fields, already in the NATIVE
    TYPES of the ClaimCase model (bools and lists), ready to assign to the claim and save.

Flow: history from the DB -> evidence requirements (reference) -> anti-injection guard
-> VLM (OpenRouter) -> output validation -> consistency layer (safe degradation).

Network / credential errors from the model PROPAGATE to the caller (so a route can turn
them into a clean 502). Garbage model output, in contrast, degrades safely to
`not_enough_information` + `manual_review_required` (never auto-approves).
"""

import json
import logging
import re

from sqlalchemy.orm import Session

from app.claims.models import ClaimCase
from app.clients.history import compute_client_history
from app.clients.models import Client
from app.policies.models import Policy
from app.core.config import get_settings
from app.llm import guard, prompts, reference, schema
from app.llm.client import OpenRouterClient

log = logging.getLogger("zipshield.llm")


# --- Public API ------------------------------------------------------------------

def analyze_claim(db: Session, claim: ClaimCase, client=None) -> dict:
    """Analyze a claim and return the 10 fields ready to persist on ClaimCase."""
    client = client or OpenRouterClient()
    history = build_user_history(db, claim.user_id, exclude_id=claim.id)
    requirements = reference.requirements_for(claim.object)
    coverage_text = _coverage_context(db, claim)
    return _review(claim.object, claim.conversation, list(claim.image_urls or []),
                   history, requirements, client, coverage_text=coverage_text)


def _coverage_context(db: Session, claim: ClaimCase) -> str:
    """Coverage of the active policy, so the LLM decides knowing what is actually covered."""
    policy_id = getattr(claim, "policy_id", None)
    if db is None or policy_id is None:
        return ""
    policy = db.get(Policy, policy_id)
    if policy is None:
        return ""
    covs = "; ".join(
        f"{c.name} (límite ${float(c.limit_amount):.0f}, deducible ${float(c.deductible):.0f})"
        for c in policy.coverages
    ) or "(sin coberturas)"
    return (f"Póliza tipo {policy.type}, estado '{policy.status}', vigencia "
            f"{policy.effective_date} a {policy.expiration_date}. Coberturas: {covs}.")


def build_user_history(db: Session, user_id: str, exclude_id=None) -> dict:
    """Thin adapter over compute_client_history for the LLM prompt.

    Same source of truth as the UI (app.clients.history); it only serializes history_flags
    to the string format the prompt expects (';'.join(...) or 'none') at the edge.
    """
    if db is None or not user_id:
        return {}
    client = db.query(Client).filter(Client.user_id == user_id).first()
    if client is None:
        return {}
    h = compute_client_history(db, client, exclude_id=exclude_id)
    return {
        "past_claim_count": h.past_claim_count,
        "last_90_days_claim_count": h.last_90_days_claim_count,
        "history_flags": ";".join(h.history_flags) if h.history_flags else "none",
        "history_summary": h.history_summary or "",
    }


# --- Internals -------------------------------------------------------------------

def _parse_json(text):
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def _context_texts(history, requirements):
    """Extra untrusted texts the guard also scans."""
    hist = []
    for k in ("history_summary", "history_flags"):
        v = str((history or {}).get(k, "")).strip()
        if v:
            hist.append(v)
    req = [str(r.get("minimum_image_evidence", "")).strip()
           for r in (requirements or []) if str(r.get("minimum_image_evidence", "")).strip()]
    return {"user_history": " ".join(hist), "evidence_requirements": " ".join(req)}


def _empty_fields():
    """All-string fields (the internal pipeline format) for when there are no usable images."""
    return {
        "evidence_standard_met": "false",
        "evidence_standard_met_reason": "No usable images for this claim.",
        "risk_flags": "manual_review_required",
        "issue_type": "unknown",
        "object_part": "unknown",
        "claim_status": "not_enough_information",
        "claim_status_justification": "No visual evidence available.",
        "supporting_image_ids": "none",
        "valid_image": "false",
        "severity": "unknown",
    }


def _to_db_fields(fields: dict) -> dict:
    """Convert the pipeline output (all strings) to ClaimCase native types.

    Convention (same as the seed): risk_flags keeps ["none"] when empty;
    supporting_image_ids becomes [] when there are no supporting images.
    """
    risk = fields.get("risk_flags", "none") or "none"
    support = fields.get("supporting_image_ids", "none") or "none"
    return {
        "evidence_standard_met": fields.get("evidence_standard_met") == "true",
        "evidence_standard_met_reason": fields.get("evidence_standard_met_reason", ""),
        "risk_flags": risk.split(";"),
        "issue_type": fields.get("issue_type", "unknown"),
        "object_part": fields.get("object_part", "unknown"),
        "claim_status": fields.get("claim_status", "not_enough_information"),
        "claim_status_justification": fields.get("claim_status_justification", ""),
        "supporting_image_ids": [] if support == "none" else support.split(";"),
        "valid_image": fields.get("valid_image") == "true",
        "severity": fields.get("severity", "unknown"),
    }


def _review(object_type, conversation, image_urls, history, requirements, client,
            coverage_text=None) -> dict:
    """DB-free core: testable by passing a fake `client` (no network)."""
    provided_ids = [f"img_{i + 1}" for i in range(len(image_urls))]
    guard_result = guard.analyze(conversation or "", None, _context_texts(history, requirements))

    # No images means no visual review is possible -> safe degradation.
    if not image_urls:
        fields = schema.enforce_consistency(_empty_fields(), guard_result, [],
                                            audit=["NO_USABLE_IMAGES"])
        return _to_db_fields(fields)

    claim_dict = {"claim_object": object_type, "user_claim": conversation}
    sys_prompt = prompts.system_prompt(spotlight=True)
    user_prompt = prompts.build_user_prompt(claim_dict, history, requirements,
                                            provided_ids, spotlight=True,
                                            coverage_text=coverage_text)
    rf = schema.output_response_format() if get_settings().llm_use_json_schema else None

    # Main call: network/credential errors PROPAGATE to the caller.
    raw_text = client.chat(sys_prompt, user_prompt, image_urls, response_format=rf)

    codes = []
    raw_status = None
    try:
        try:
            parsed = _parse_json(raw_text)
        except json.JSONDecodeError:
            strict = user_prompt + ("\n\nIMPORTANT: respond with ONLY a valid JSON object, "
                                    "no prose, and escape any inner quotes.")
            # This retry can also fail on network/credentials, not just invalid JSON —
            # that case must propagate like the main call above, not be treated as
            # invalid model output (see the explicit `except RuntimeError` below).
            parsed = _parse_json(client.chat(sys_prompt, strict, image_urls, response_format=rf))
        fields = schema.validate(parsed, object_type, provided_ids)
        raw_status = fields["claim_status"]
        # The model returned JSON but omitted the main decision key.
        if not (isinstance(parsed, dict) and "claim_status" in parsed):
            codes.append("OUTPUT_INCOMPLETE")
            fields["risk_flags"] = schema.merge_flags(fields.get("risk_flags", "none"),
                                                      ["manual_review_required"])
    except RuntimeError:
        # Provider network/credential errors: propagate, never degrade.
        raise
    except Exception as e:   # invalid model output -> safe degradation
        log.warning("Invalid model output: %s", e)
        fields = schema.validate({}, object_type, provided_ids)
        fields["claim_status"] = "not_enough_information"
        fields["claim_status_justification"] = "Error while processing the claim."
        fields["risk_flags"] = "manual_review_required"
        codes.append("MODEL_ERROR")

    # Deterministic layer: merges guard flags + consistency rules (never auto-approves).
    fields = schema.enforce_consistency(fields, guard_result, provided_ids, audit=codes)
    if not codes:
        codes.append("CLEAN")
    log.info("Claim analyzed: raw=%s final=%s codes=%s",
             raw_status, fields.get("claim_status"), codes)
    return _to_db_fields(fields)
