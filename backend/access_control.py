"""
Access Control Engine — Fase 4.

Centralizes all access decision logic:
  - Rule evaluation (is_active, time window, access_level)
  - Gate trigger via GateAdapter factory
  - AccessLog persistence

Called from the AI pipeline (face_recognized) and from the guarita route (manual approval).
"""

import json
import datetime
from typing import Optional

# Hierarchy for access level comparison
_LEVEL_ORDER = {"restricted": 0, "standard": 1, "admin": 2}


# ── Rule evaluation ────────────────────────────────────────────────────────────

def _check_time_rules(rules: dict) -> tuple[bool, str]:
    if not rules:
        return True, "ok"
    now = datetime.datetime.now()
    allowed_days = rules.get("allowed_days")
    if allowed_days is not None and now.weekday() not in allowed_days:
        return False, f"dia_semana_nao_permitido"
    start_str = rules.get("start_time")
    end_str = rules.get("end_time")
    if start_str and end_str:
        start = datetime.time.fromisoformat(start_str)
        end = datetime.time.fromisoformat(end_str)
        current = now.time().replace(second=0, microsecond=0)
        if not (start <= current <= end):
            return False, f"fora_do_horario ({start_str}–{end_str})"
    return True, "ok"


def _check_access_level(person_level: str, min_level: Optional[str]) -> tuple[bool, str]:
    if not min_level:
        return True, "ok"
    p = _LEVEL_ORDER.get(person_level, 0)
    m = _LEVEL_ORDER.get(min_level, 0)
    if p < m:
        return False, f"nivel_insuficiente ({person_level} < {min_level})"
    return True, "ok"


def evaluate_access(person, device) -> tuple[bool, str]:
    """Returns (granted: bool, reason: str)."""
    if not person.is_active:
        return False, "pessoa_inativa"

    rules = {}
    if device.time_rules:
        try:
            rules = json.loads(device.time_rules)
        except Exception:
            pass

    ok, reason = _check_time_rules(rules)
    if not ok:
        return False, reason

    ok, reason = _check_access_level(person.access_level, device.min_access_level)
    if not ok:
        return False, reason

    return True, "ok"


# ── Gate trigger ───────────────────────────────────────────────────────────────

def trigger_gate_for_device(device, db) -> bool:
    """Trigger the gate linked to this device. Returns True if pulse sent successfully."""
    if not device.gate_id:
        return False
    try:
        import crud
        gate = crud.get_gate(db, device.gate_id)
        if not gate or not gate.is_active:
            return False
        from adapters.gate.factory import get_gate_adapter
        adapter = get_gate_adapter(gate)
        success = adapter.trigger()
        if success:
            crud.update_gate_status(db, gate.id, "moving")
        return success
    except Exception as e:
        print(f"[access_control] gate trigger error: {e}")
        return False


# ── Main entry points ──────────────────────────────────────────────────────────

def handle_face_access(db, person, device, confidence: float, camera_id: int) -> dict:
    """
    Full access flow for a recognized person.
    Evaluates rules → logs to AccessLog → triggers gate if granted.
    Returns result dict (consumed by AI pipeline and by /access/check route).
    """
    import crud
    import schemas

    granted, reason = evaluate_access(person, device)

    log = crud.create_access_log(db, schemas.AccessLogCreate(
        person_id=person.id,
        device_id=device.id,
        result="granted" if granted else "denied",
        method="facial",
        confidence=round(confidence * 100, 1),
        direction="in",
        notes=None if granted else reason,
    ))

    gate_triggered = False
    if granted:
        gate_triggered = trigger_gate_for_device(device, db)

    return {
        "granted": granted,
        "reason": reason,
        "person_id": person.id,
        "person_name": person.name,
        "confidence": round(confidence, 3),
        "gate_triggered": gate_triggered,
        "log_id": log.id,
    }


def handle_manual_open(db, device, operator_notes: Optional[str] = None) -> dict:
    """
    Manual gate open by guarita operator (no person match required).
    Logs as method=manual.
    """
    import crud
    import schemas

    gate_triggered = trigger_gate_for_device(device, db)

    log = crud.create_access_log(db, schemas.AccessLogCreate(
        device_id=device.id,
        result="granted",
        method="manual",
        direction="in",
        notes=operator_notes,
    ))

    return {
        "granted": True,
        "gate_triggered": gate_triggered,
        "log_id": log.id,
    }
