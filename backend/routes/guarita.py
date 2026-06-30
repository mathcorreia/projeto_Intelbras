"""
Módulo Guarita — Fase 5.

Responsabilidades:
  - Fila de faces desconhecidas pendentes de revisão pelo operador
  - Pré-cadastro e aprovação de visitantes
  - Abertura manual de portão após aprovação
  - SSE (Server-Sent Events) para alertas em tempo real no frontend
    (substituído por STOMP WebSocket na Fase 8, quando o Java backendPerm estiver pronto)
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.core import SessionLocal
from auth.jwt_middleware import get_current_tenant_id
import crud
import schemas
import access_control

router = APIRouter(prefix="/guarita", tags=["guarita"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Fila de faces desconhecidas ────────────────────────────────────────────────

@router.get("/queue")
def get_alert_queue(
    limit: int = 50,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    events = crud.get_unknown_face_events(db, tenant_id=tenant_id, limit=limit)
    result = []
    for ev in events:
        data = {}
        if ev.event_data:
            try:
                data = json.loads(ev.event_data)
            except Exception:
                pass
        result.append({
            "event_id": ev.id,
            "event_type": ev.event_type,
            "timestamp": ev.timestamp.isoformat(),
            "camera_id": ev.camera_id,
            "face_image_path": ev.face_image_path,
            "confidence": data.get("confidence"),
            "emotion": data.get("emotion"),
            "device_id": data.get("device_id"),
        })
    return result


# ── SSE — alertas em tempo real ────────────────────────────────────────────────

@router.get("/alerts/stream")
async def stream_alerts(db: Session = Depends(get_db)):
    """
    Server-Sent Events: envia novos alertas de face desconhecida ao frontend.
    Migrar para STOMP WebSocket na Fase 8.
    """
    async def generator():
        last_id = 0
        existing = crud.get_unknown_face_events(db, limit=1)
        if existing:
            last_id = existing[0].id

        yield "retry: 3000\n\n"

        while True:
            new_events = crud.get_unknown_face_events(db, after_id=last_id, limit=20)
            for ev in sorted(new_events, key=lambda e: e.id):
                last_id = ev.id
                data = {}
                if ev.event_data:
                    try:
                        data = json.loads(ev.event_data)
                    except Exception:
                        pass
                payload = json.dumps({
                    "event_id": ev.id,
                    "event_type": ev.event_type,
                    "timestamp": ev.timestamp.isoformat(),
                    "camera_id": ev.camera_id,
                    "face_image_path": ev.face_image_path,
                    "confidence": data.get("confidence"),
                    "emotion": data.get("emotion"),
                    "device_id": data.get("device_id"),
                })
                yield f"data: {payload}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(generator(), media_type="text/event-stream")


# ── Aprovar / Negar face desconhecida ──────────────────────────────────────────

class GuaritaDecisionRequest(BaseModel):
    device_id: Optional[int] = None
    notes: Optional[str] = None


@router.post("/approve/{event_id}")
def approve_unknown_face(event_id: int, body: GuaritaDecisionRequest, db: Session = Depends(get_db)):
    """Operador aprova entrada de face desconhecida."""
    from database import models
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    if event.event_type not in ("unknown_face", "visitor_detected"):
        raise HTTPException(status_code=400, detail="Evento não é de face desconhecida")

    result = {"approved": True, "event_id": event_id, "gate_triggered": False, "log_id": None}

    if body.device_id:
        device = crud.get_access_device(db, body.device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
        open_result = access_control.handle_manual_open(
            db=db, device=device,
            operator_notes=f"Aprovação manual guarita. Evento #{event_id}. {body.notes or ''}"
        )
        result["gate_triggered"] = open_result["gate_triggered"]
        result["log_id"] = open_result["log_id"]

    return result


@router.post("/deny/{event_id}")
def deny_unknown_face(event_id: int, body: GuaritaDecisionRequest, db: Session = Depends(get_db)):
    """Operador nega entrada. Registra log de acesso negado."""
    from database import models
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    log = crud.create_access_log(db, schemas.AccessLogCreate(
        device_id=body.device_id,
        result="denied",
        method="manual",
        direction="in",
        notes=f"Negação manual guarita. Evento #{event_id}. {body.notes or ''}",
    ))
    return {"denied": True, "event_id": event_id, "log_id": log.id}


# ── Gestão de Visitantes ───────────────────────────────────────────────────────

@router.get("/visitors", response_model=list[schemas.Visitor])
def list_guarita_visitors(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.get_active_visitors(db, tenant_id=tenant_id)


@router.post("/visitors", response_model=schemas.Visitor)
def pre_register_visitor(
    visitor: schemas.VisitorCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.create_visitor(db, visitor, tenant_id=tenant_id)


@router.patch("/visitors/{visitor_id}/approve", response_model=schemas.Visitor)
def approve_visitor(visitor_id: int, db: Session = Depends(get_db)):
    visitor = crud.update_visitor_status(db, visitor_id, "approved")
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitante não encontrado")
    return visitor


@router.patch("/visitors/{visitor_id}/deny", response_model=schemas.Visitor)
def deny_visitor(visitor_id: int, db: Session = Depends(get_db)):
    visitor = crud.update_visitor_status(db, visitor_id, "denied")
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitante não encontrado")
    return visitor
