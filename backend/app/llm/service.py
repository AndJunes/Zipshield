"""Orquesta el análisis de un claim con el LLM (adaptación de agent/reviewer.py del reto).

Pieza pública:
    analyze_claim(db, claim) -> dict con los 10 campos del análisis, ya en los TIPOS NATIVOS
    del modelo ClaimCase (bools y listas), listos para asignar al claim y guardar.

Flujo: historial desde la BD -> requisitos de evidencia (reference) -> guardia anti-inyección
-> VLM (OpenRouter) -> validación de salida -> capa de consistencia (degradación segura).

Errores de red / credenciales del modelo se PROPAGAN al llamador (para que una futura ruta
los traduzca a un 502 limpio). La salida basura del modelo, en cambio, degrada de forma
segura a `not_enough_information` + `manual_review_required` (nunca auto-aprueba).
"""

import json
import logging
import re

from sqlalchemy.orm import Session

from app.claims.models import ClaimCase
from app.clients.history import compute_client_history
from app.clients.models import Client
from app.core.config import get_settings
from app.llm import guard, prompts, reference, schema
from app.llm.client import OpenRouterClient

log = logging.getLogger("zipshield.llm")


# --- API pública -----------------------------------------------------------------

def analyze_claim(db: Session, claim: ClaimCase, client=None) -> dict:
    """Analiza un claim y devuelve los 10 campos listos para persistir en ClaimCase."""
    client = client or OpenRouterClient()
    history = build_user_history(db, claim.user_id, exclude_id=claim.id)
    requirements = reference.requirements_for(claim.object)
    return _review(claim.object, claim.conversation, list(claim.image_urls or []),
                   history, requirements, client)


def build_user_history(db: Session, user_id: str, exclude_id=None) -> dict:
    """Adaptador delgado sobre compute_client_history para el prompt del LLM.

    Misma fuente de verdad que la UI (app.clients.history); solo serializa history_flags
    al formato-string que espera el prompt (';'.join(...) o 'none') en el borde.
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


# --- Internos --------------------------------------------------------------------

def _parse_json(text):
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def _context_texts(history, requirements):
    """Textos no confiables extra que el guardia también escanea."""
    hist = []
    for k in ("history_summary", "history_flags"):
        v = str((history or {}).get(k, "")).strip()
        if v:
            hist.append(v)
    req = [str(r.get("minimum_image_evidence", "")).strip()
           for r in (requirements or []) if str(r.get("minimum_image_evidence", "")).strip()]
    return {"user_history": " ".join(hist), "evidence_requirements": " ".join(req)}


def _empty_fields():
    """Campos (en forma de strings, como el reto) para cuando no hay imágenes utilizables."""
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
    """Convierte la salida del reto (todo strings) a los tipos nativos de ClaimCase.

    Convención (igual que el seed): risk_flags conserva ["none"] cuando está vacío;
    supporting_image_ids se vuelve [] cuando no hay imágenes de soporte.
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


def _review(object_type, conversation, image_urls, history, requirements, client) -> dict:
    """Núcleo sin BD: testeable pasando un `client` falso (sin red)."""
    provided_ids = [f"img_{i + 1}" for i in range(len(image_urls))]
    guard_result = guard.analyze(conversation or "", None, _context_texts(history, requirements))

    # Sin imágenes no se puede revisar visualmente -> degradación segura.
    if not image_urls:
        fields = schema.enforce_consistency(_empty_fields(), guard_result, [],
                                            audit=["NO_USABLE_IMAGES"])
        return _to_db_fields(fields)

    claim_dict = {"claim_object": object_type, "user_claim": conversation}
    sys_prompt = prompts.system_prompt(spotlight=True)
    user_prompt = prompts.build_user_prompt(claim_dict, history, requirements,
                                            provided_ids, spotlight=True)
    rf = schema.output_response_format() if get_settings().llm_use_json_schema else None

    # Llamada principal: los errores de red/credenciales se PROPAGAN al llamador.
    raw_text = client.chat(sys_prompt, user_prompt, image_urls, response_format=rf)

    codes = []
    raw_status = None
    try:
        try:
            parsed = _parse_json(raw_text)
        except json.JSONDecodeError:
            strict = user_prompt + ("\n\nIMPORTANT: respond with ONLY a valid JSON object, "
                                    "no prose, and escape any inner quotes.")
            parsed = _parse_json(client.chat(sys_prompt, strict, image_urls, response_format=rf))
        fields = schema.validate(parsed, object_type, provided_ids)
        raw_status = fields["claim_status"]
        # El modelo respondió JSON pero omitió la clave de decisión principal.
        if not (isinstance(parsed, dict) and "claim_status" in parsed):
            codes.append("OUTPUT_INCOMPLETE")
            fields["risk_flags"] = schema.merge_flags(fields.get("risk_flags", "none"),
                                                      ["manual_review_required"])
    except Exception as e:   # salida del modelo inválida -> degradación segura
        log.warning("Salida del modelo inválida: %s", e)
        fields = schema.validate({}, object_type, provided_ids)
        fields["claim_status"] = "not_enough_information"
        fields["claim_status_justification"] = "Error while processing the claim."
        fields["risk_flags"] = "manual_review_required"
        codes.append("MODEL_ERROR")

    # Capa determinista: fusiona flags del guardia + reglas de consistencia (nunca auto-aprueba).
    fields = schema.enforce_consistency(fields, guard_result, provided_ids, audit=codes)
    if not codes:
        codes.append("CLEAN")
    log.info("Claim analizado: raw=%s final=%s codes=%s",
             raw_status, fields.get("claim_status"), codes)
    return _to_db_fields(fields)
