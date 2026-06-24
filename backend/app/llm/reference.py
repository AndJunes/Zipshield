"""Requisitos mínimos de evidencia por tipo de objeto.

Portado de `dataset/evidence_requirements.csv` del reto de HackerRank. Es dato de
REFERENCIA / política (no cambia por usuario), por eso vive como constante y no en la BD.
Si más adelante quieres editarlo desde la UI, se puede promover a una tabla de Postgres
con su propio seed (eso sería una fase posterior).

`requirements_for(obj)` devuelve los requisitos del objeto + los generales ("all"), igual
que hacía la clase Context del reto.
"""

EVIDENCE_REQUIREMENTS = {
    "all": [
        {"requirement_id": "REQ_GENERAL_OBJECT_PART", "applies_to": "general claim review",
         "minimum_image_evidence": "The claimed object and relevant part should be visible clearly enough to inspect the claimed condition."},
        {"requirement_id": "REQ_GENERAL_MULTI_IMAGE", "applies_to": "multi-image rows",
         "minimum_image_evidence": "Each submitted image should be considered separately; at least one relevant image should show the claimed object or part clearly enough to evaluate the claim."},
        {"requirement_id": "REQ_REVIEW_TRUST", "applies_to": "reviewability",
         "minimum_image_evidence": "The submitted images should provide visual evidence that is usable, relevant to the claim, and grounded in the claimed object."},
    ],
    "car": [
        {"requirement_id": "REQ_CAR_BODY_PANEL", "applies_to": "dent or scratch",
         "minimum_image_evidence": "The claimed car panel or bumper should be visible from an angle where surface marks or deformation can be assessed."},
        {"requirement_id": "REQ_CAR_GLASS_LIGHT_MIRROR", "applies_to": "crack, broken, or missing part",
         "minimum_image_evidence": "The claimed glass, light, mirror, or component should be visible clearly enough to inspect cracks, breakage, or missing parts."},
        {"requirement_id": "REQ_CAR_IDENTITY_OR_SIDE", "applies_to": "vehicle identity or orientation",
         "minimum_image_evidence": "When the claim depends on vehicle identity, side, or orientation, the image set should show enough context to match the claimed vehicle and part."},
    ],
    "laptop": [
        {"requirement_id": "REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD", "applies_to": "screen, keyboard, or trackpad",
         "minimum_image_evidence": "The claimed laptop screen, keyboard, or trackpad area should be visible clearly enough to inspect cracks, stains, missing keys, or surface damage."},
        {"requirement_id": "REQ_LAPTOP_BODY_HINGE_PORT", "applies_to": "hinge, lid, corner, body, or port",
         "minimum_image_evidence": "The claimed laptop hinge, lid, corner, body, base, or port should be visible with enough context to identify the relevant laptop part."},
    ],
    "package": [
        {"requirement_id": "REQ_PACKAGE_EXTERIOR", "applies_to": "crushed, torn, or seal damage",
         "minimum_image_evidence": "The package exterior and claimed side, corner, flap, or seal should be visible clearly enough to inspect packaging damage."},
        {"requirement_id": "REQ_PACKAGE_LABEL_OR_STAIN", "applies_to": "water, stain, or label damage",
         "minimum_image_evidence": "The affected package surface or label should be visible clearly enough to assess stain, water damage, label readability, or label damage."},
        {"requirement_id": "REQ_PACKAGE_CONTENTS", "applies_to": "contents or inner item",
         "minimum_image_evidence": "The opened package and relevant contents area should be visible clearly enough to assess missing or damaged items."},
    ],
}


def requirements_for(claim_object):
    """Requisitos del objeto + los generales ('all')."""
    obj = str(claim_object).strip().lower()
    return EVIDENCE_REQUIREMENTS.get(obj, []) + EVIDENCE_REQUIREMENTS.get("all", [])
