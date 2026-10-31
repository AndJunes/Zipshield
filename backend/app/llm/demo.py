"""Canned analyses for demo deployments (DEMO_MODE=true).

The public demo can't ship a real OpenRouter key, so this produces an honest,
deterministic review with the same shape as the model's output. The text says
it's canned; nothing pretends to have looked at the photos.
"""

from app.claims.models import ClaimCase

_DEMO_NOTE = (
    "Demo mode: this is a precomputed review. In the full setup, a vision model "
    "inspects the photos against the evidence requirements for the object type, "
    "the client's claim history and the policy coverage."
)


def demo_analysis(claim: ClaimCase) -> dict:
    """Return the 10 analysis fields without calling any external service."""
    if not claim.image_urls:
        return {
            "evidence_standard_met": False,
            "evidence_standard_met_reason": f"No photos attached. {_DEMO_NOTE}",
            "risk_flags": ["none"],
            "issue_type": "unknown",
            "object_part": "unknown",
            "claim_status": "not_enough_information",
            "claim_status_justification": (
                f"A claim can't be reviewed without evidence. {_DEMO_NOTE}"
            ),
            "supporting_image_ids": [],
            "valid_image": False,
            "severity": "unknown",
        }
    return {
        "evidence_standard_met": True,
        "evidence_standard_met_reason": f"Photos attached for the claimed object. {_DEMO_NOTE}",
        "risk_flags": ["none"],
        "issue_type": "accidental_damage",
        "object_part": "body",
        "claim_status": "supported",
        "claim_status_justification": (
            f"The attached evidence is consistent with the reported incident. {_DEMO_NOTE}"
        ),
        "supporting_image_ids": [f"img_{index + 1}" for index in range(len(claim.image_urls))],
        "valid_image": True,
        "severity": "medium",
    }
