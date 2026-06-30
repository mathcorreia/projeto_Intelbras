from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.core import SessionLocal
from auth.jwt_middleware import get_current_tenant_id
import crud
import schemas
import access_control

router = APIRouter(prefix="/access", tags=["access"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Dispositivos ---

@router.get("/devices", response_model=list[schemas.AccessDevice])
def list_devices(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.get_access_devices(db, tenant_id=tenant_id)


@router.post("/devices", response_model=schemas.AccessDevice)
def create_device(
    device: schemas.AccessDeviceCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.create_access_device(db, device, tenant_id=tenant_id)


@router.get("/devices/{device_id}", response_model=schemas.AccessDevice)
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = crud.get_access_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    return device


@router.put("/devices/{device_id}", response_model=schemas.AccessDevice)
def update_device(device_id: int, data: schemas.AccessDeviceUpdate, db: Session = Depends(get_db)):
    device = crud.update_access_device(db, device_id, data)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    return device


@router.delete("/devices/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    success = crud.delete_access_device(db, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    return {"message": "Dispositivo removido com sucesso"}


# --- Logs de Acesso ---

@router.get("/logs", response_model=list[schemas.AccessLog])
def list_access_logs(
    person_id: int = None,
    device_id: int = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.get_access_logs(db, person_id=person_id, device_id=device_id, tenant_id=tenant_id, limit=limit)


@router.post("/logs", response_model=schemas.AccessLog)
def create_access_log(
    log: schemas.AccessLogCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.create_access_log(db, log, tenant_id=tenant_id)


# ── Controle de acesso integrado ──────────────────────────────────────────────

class AccessCheckRequest(BaseModel):
    person_id: int
    device_id: int


@router.post("/check")
def check_access(body: AccessCheckRequest, db: Session = Depends(get_db)):
    """Evaluate access rules for a person + device pair, trigger gate if granted."""
    person = crud.get_person(db, body.person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    device = crud.get_access_device(db, body.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")

    return access_control.handle_face_access(
        db=db, person=person, device=device, confidence=1.0, camera_id=device.camera_id or 0
    )


class ManualOpenRequest(BaseModel):
    notes: str = None


@router.post("/devices/{device_id}/manual-open")
def manual_open(device_id: int, body: ManualOpenRequest = ManualOpenRequest(), db: Session = Depends(get_db)):
    """Guarita operator manually opens the gate linked to a device."""
    device = crud.get_access_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    if not device.gate_id:
        raise HTTPException(status_code=400, detail="Nenhum portão vinculado a este dispositivo")
    return access_control.handle_manual_open(db=db, device=device, operator_notes=body.notes)
