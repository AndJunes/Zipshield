"""Output schema and validation. Mirrors the HackerRank challenge contract exactly.

Ported verbatim from the challenge: the allowed values, coercion and the deterministic
consistency layer (safe degradation) are security-relevant and were kept unchanged.
"""

import re

# Output columns in the EXACT required order.
OUTPUT_COLUMNS = [
    "user_id",
    "image_paths",
    "user_claim",
    "claim_object",
    "evidence_standard_met",
    "evidence_standard_met_reason",
    "risk_flags",
    "issue_type",
    "object_part",
    "claim_status",
    "claim_status_justification",
    "supporting_image_ids",
    "valid_image",
    "severity",
]

# Columns copied straight from the input.
PASSTHROUGH = ["user_id", "image_paths", "user_claim", "claim_object"]

# The 10 columns produced by the model.
MODEL_FIELDS = [c for c in OUTPUT_COLUMNS if c not in PASSTHROUGH]

# --- Allowed values ---
CLAIM_STATUS = ["supported", "contradicted", "not_enough_information"]

ISSUE_TYPE = [
    "dent", "scratch", "crack", "glass_shatter", "broken_part", "missing_part",
    "torn_packaging", "crushed_packaging", "water_damage", "stain", "none", "unknown",
]

OBJECT_PARTS = {
    "car": ["front_bumper", "rear_bumper", "door", "hood", "windshield", "side_mirror",
            "headlight", "taillight", "fender", "quarter_panel", "body", "unknown"],
    "laptop": ["screen", "keyboard", "trackpad", "hinge", "lid", "corner", "port",
               "base", "body", "unknown"],
    "package": ["box", "package_corner", "package_side", "seal", "label", "contents",
                "item", "unknown"],
}

RISK_FLAGS = [
    "none", "blurry_image", "cropped_or_obstructed", "low_light_or_glare", "wrong_angle",
    "wrong_object", "wrong_object_part", "damage_not_visible", "claim_mismatch",
    "possible_manipulation", "non_original_image", "text_instruction_present",
    "user_history_risk", "manual_review_required",
]

SEVERITY = ["none", "low", "medium", "high", "unknown"]

# Machine-readable reason codes recorded in the audit/log.
REASON_CODES = [
    "CLEAN", "INJECTION_DETECTED", "SUPPORTED_WITHOUT_EVIDENCE",
    "CONTRADICTED_WITHOUT_EVIDENCE", "HIGH_SEVERITY_NO_DAMAGE",
    "STATUS_EVIDENCE_MISMATCH", "OUTPUT_MANIPULATION_ECHO",
    "OUTPUT_INCOMPLETE", "NO_USABLE_IMAGES", "MODEL_ERROR",
]


def output_response_format():
    """OpenRouter strict json_schema for the 10 model-produced fields.

    Enforces exact conformance (enums + required + additionalProperties:false) so the model
    cannot return malformed or missing fields. Format-level only: it does not improve the
    semantic accuracy of the labels. Provider-dependent (Gemini supported); the application
    keeps `validate` + the reprompt fallback as a defensive net.
    """
    s = {"type": "string"}
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "claim_review",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "evidence_standard_met": {"type": "boolean"},
                    "evidence_standard_met_reason": s,
                    "risk_flags": {"type": "array", "items": {"type": "string", "enum": RISK_FLAGS}},
                    "issue_type": {"type": "string", "enum": ISSUE_TYPE},
                    "object_part": s,   # allowed set depends on claim_object; coerced in validate()
                    "claim_status": {"type": "string", "enum": CLAIM_STATUS},
                    "claim_status_justification": s,
                    "supporting_image_ids": {"type": "array", "items": {"type": "string"}},
                    "valid_image": {"type": "boolean"},
                    "severity": {"type": "string", "enum": SEVERITY},
                },
                "required": MODEL_FIELDS,
                "additionalProperties": False,
            },
        },
    }


def _as_bool_str(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return "true" if str(value).strip().lower() in ("true", "1", "yes") else "false"


def _coerce(value, allowed, default):
    v = str(value).strip().lower()
    return v if v in allowed else default


def _as_list(value):
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    s = str(value).strip()
    if not s:
        return []
    return [p.strip() for p in s.replace(",", ";").split(";") if p.strip()]


def normalize_risk_flags(value):
    flags = [f.lower() for f in _as_list(value) if f.lower() in RISK_FLAGS]
    flags = list(dict.fromkeys(flags))          # dedup, keep order
    flags = [f for f in flags if f != "none"]   # 'none' only when alone
    return ";".join(flags) if flags else "none"


def normalize_supporting_ids(value, provided_ids):
    ids = [i for i in _as_list(value) if i in provided_ids]
    ids = list(dict.fromkeys(ids))
    return ";".join(ids) if ids else "none"


def validate(raw, claim_object, provided_ids):
    """Normalize the raw model output to the 10 columns, respecting the allowed values."""
    claim_object = str(claim_object).strip().lower()
    parts = OBJECT_PARTS.get(claim_object, OBJECT_PARTS["car"])
    out = {
        "evidence_standard_met": _as_bool_str(raw.get("evidence_standard_met", False)),
        "evidence_standard_met_reason": str(raw.get("evidence_standard_met_reason", "")).strip(),
        "risk_flags": normalize_risk_flags(raw.get("risk_flags", "none")),
        "issue_type": _coerce(raw.get("issue_type", "unknown"), ISSUE_TYPE, "unknown"),
        "object_part": _coerce(raw.get("object_part", "unknown"), parts, "unknown"),
        "claim_status": _coerce(raw.get("claim_status", "not_enough_information"),
                                CLAIM_STATUS, "not_enough_information"),
        "claim_status_justification": str(raw.get("claim_status_justification", "")).strip(),
        "supporting_image_ids": normalize_supporting_ids(
            raw.get("supporting_image_ids", "none"), provided_ids),
        "valid_image": _as_bool_str(raw.get("valid_image", False)),
        "severity": _coerce(raw.get("severity", "unknown"), SEVERITY, "unknown"),
    }
    # Principled coherence: no visible issue => no severity.
    if out["issue_type"] == "none":
        out["severity"] = "none"
    return out


# --- Deterministic safety layer: flag merge + consistency + safe fallback ---

def merge_flags(*flag_sources):
    """Merge several risk_flags sources (';'/',' string or list) into a normalized string."""
    combined = []
    for src in flag_sources:
        combined.extend(_as_list(src))
    return normalize_risk_flags(combined)


_ECHO_RE = re.compile(r"as (requested|instructed)|per your instruction|as you (said|asked)", re.IGNORECASE)


def enforce_consistency(fields, guard_result=None, provided_ids=None, audit=None):
    """
    Deterministic consistency and SAFE DEGRADATION layer. Always runs after the VLM (and
    in the fallbacks too). Merges the deterministic detector's (guard) signals with the
    model's and applies rules that NEVER auto-approve under risk.

    `guard_result`: dict from app.llm.guard.analyze (or None).
    `audit`: optional list; the reason codes that fired are appended to it (for the log).
    Returns the adjusted `fields` (same 10 keys; the output schema is unchanged).
    """
    fields = dict(fields)
    guard_result = guard_result or {}
    extra_flags = list(guard_result.get("flags", []))
    reasons = []
    codes = audit if isinstance(audit, list) else []

    # 1) Prompt injection detected by the guard -> degrade and flag (survives runtime).
    if guard_result.get("detected"):
        extra_flags += ["text_instruction_present", "manual_review_required"]
        codes.append("INJECTION_DETECTED")
        if fields.get("claim_status") == "supported":
            fields["claim_status"] = "not_enough_information"
            reasons.append("possible prompt injection detected by the deterministic guard")

    # 2) Groundedness: a decision must cite a supporting image.
    status = fields.get("claim_status")
    if status == "supported" and fields.get("supporting_image_ids", "none") == "none":
        fields["claim_status"] = "not_enough_information"
        extra_flags.append("manual_review_required")
        reasons.append("supported without supporting_image_ids")
        codes.append("SUPPORTED_WITHOUT_EVIDENCE")
    elif status == "contradicted" and fields.get("supporting_image_ids", "none") == "none":
        fields["claim_status"] = "not_enough_information"
        extra_flags.append("manual_review_required")
        reasons.append("contradicted without supporting_image_ids")
        codes.append("CONTRADICTED_WITHOUT_EVIDENCE")

    # 3) High severity without visible damage is inconsistent -> manual review.
    current_flags = _as_list(fields.get("risk_flags"))
    if fields.get("severity") == "high" and (
        fields.get("issue_type") == "none" or "damage_not_visible" in current_flags
    ):
        extra_flags.append("manual_review_required")
        reasons.append("severity=high without visible damage")
        codes.append("HIGH_SEVERITY_NO_DAMAGE")

    # 4) A firm decision with evidence_standard_met=false is shaky -> manual review.
    if fields.get("claim_status") in ("supported", "contradicted") and \
            fields.get("evidence_standard_met") == "false":
        extra_flags.append("manual_review_required")
        reasons.append("decision without evidence standard met")
        codes.append("STATUS_EVIDENCE_MISMATCH")

    # 5) The output echoing injected instructions -> possible manipulation.
    just = fields.get("claim_status_justification", "") or ""
    if "«" in just or _ECHO_RE.search(just):
        extra_flags += ["possible_manipulation", "manual_review_required"]
        reasons.append("model output echoes injected instructions")
        codes.append("OUTPUT_MANIPULATION_ECHO")

    if extra_flags:
        fields["risk_flags"] = merge_flags(fields.get("risk_flags", "none"), extra_flags)

    if reasons:
        note = " | review: " + "; ".join(reasons)
        fields["claim_status_justification"] = (just.strip() + note).strip()[:600]

    if isinstance(audit, list):
        audit[:] = list(dict.fromkeys(audit))   # dedup in place

    return fields
