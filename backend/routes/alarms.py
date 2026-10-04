from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.core import SessionLocal
from adapters.alarm.intelbras_http_adapter import IntelbrasHTTPAdapter
from auth.jwt_middleware import get_current_tenant_id
import crud
import schemas

router = APIRouter(prefix="/alarms", tags=["alarms"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Centrais ──────────────────────────────────────────────────────────────────

@router.get("/centrals", response_model=list[schemas.AlarmCentral])
def list_centrals(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.get_alarm_centrals(db, tenant_id=tenant_id)


@router.post("/centrals", response_model=schemas.AlarmCentral)
def create_central(
    central: schemas.AlarmCentralCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.create_alarm_central(db, central, tenant_id=tenant_id)


@router.get("/centrals/{central_id}", response_model=schemas.AlarmCentral)
def get_central(central_id: int, db: Session = Depends(get_db)):
    central = crud.get_alarm_central(db, central_id)
    if not central:
        raise HTTPException(status_code=404, detail="Central não encontrada")
    return central


@router.put("/centrals/{central_id}", response_model=schemas.AlarmCentral)
def update_central(central_id: int, data: schemas.AlarmCentralUpdate, db: Session = Depends(get_db)):
    central = crud.update_alarm_central(db, central_id, data)
    if not central:
        raise HTTPException(status_code=404, detail="Central não encontrada")
    return central


@router.delete("/centrals/{central_id}")
def delete_central(central_id: int, db: Session = Depends(get_db)):
    if not crud.delete_alarm_central(db, central_id):
        raise HTTPException(status_code=404, detail="Central não encontrada")
    return {"message": "Central removida com sucesso"}


# ── Comandos de controle (via HTTP — AMT com IP) ──────────────────────────────

@router.post("/centrals/{central_id}/arm")
def arm_central(central_id: int, partition: int = 1, db: Session = Depends(get_db)):
    central = _get_or_404(db, central_id)
    adapter = _build_http_adapter(central)
    success = adapter.arm(partition)
    return {"success": success, "message": "Arme enviado" if success else "Central sem IP ou sem suporte HTTP"}


@router.post("/centrals/{central_id}/disarm")
def disarm_central(central_id: int, partition: int = 1, db: Session = Depends(get_db)):
    central = _get_or_404(db, central_id)
    adapter = _build_http_adapter(central)
    success = adapter.disarm(partition)
    return {"success": success, "message": "Desarme enviado" if success else "Central sem IP ou sem suporte HTTP"}


@router.post("/centrals/{central_id}/arm-stay")
def arm_stay(central_id: int, partition: int = 1, db: Session = Depends(get_db)):
    central = _get_or_404(db, central_id)
    adapter = _build_http_adapter(central)
    success = adapter.arm_stay(partition)
    return {"success": success, "message": "Arme Presente enviado" if success else "Falhou"}


@router.get("/centrals/{central_id}/status")
def get_central_status(central_id: int, db: Session = Depends(get_db)):
    central = _get_or_404(db, central_id)
    if not central.ip:
        return {"online": False, "reason": "Central sem IP cadastrado (usa TCP passivo)"}
    adapter = _build_http_adapter(central)
    return adapter.get_status()


# ── Zonas ─────────────────────────────────────────────────────────────────────

@router.get("/centrals/{central_id}/zones", response_model=list[schemas.AlarmZone])
def list_zones(
    central_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.get_alarm_zones(db, central_id, tenant_id=tenant_id)


@router.post("/zones", response_model=schemas.AlarmZone)
def create_zone(
    zone: schemas.AlarmZoneCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    if not crud.get_alarm_central(db, zone.central_id):
        raise HTTPException(status_code=404, detail="Central não encontrada")
    return crud.create_alarm_zone(db, zone, tenant_id=tenant_id)


@router.put("/zones/{zone_id}", response_model=schemas.AlarmZone)
def update_zone(zone_id: int, data: schemas.AlarmZoneUpdate, db: Session = Depends(get_db)):
    zone = crud.update_alarm_zone(db, zone_id, data)
    if not zone:
        raise HTTPException(status_code=404, detail="Zona não encontrada")
    return zone


@router.patch("/zones/{zone_id}/bypass")
def toggle_bypass(zone_id: int, db: Session = Depends(get_db)):
    zone = crud.get_alarm_zone(db, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zona não encontrada")
    updated = crud.update_alarm_zone(db, zone_id, schemas.AlarmZoneUpdate(is_bypassed=not zone.is_bypassed))
    return {"zone_id": zone_id, "is_bypassed": updated.is_bypassed}


# ── Eventos ───────────────────────────────────────────────────────────────────

@router.get("/events", response_model=list[schemas.AlarmEvent])
def list_alarm_events(
    central_id: int = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.get_alarm_events(db, central_id=central_id, tenant_id=tenant_id, limit=limit)


@router.post("/events", response_model=schemas.AlarmEvent)
def create_alarm_event(
    event: schemas.AlarmEventCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.create_alarm_event(db, event, tenant_id=tenant_id)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(db, central_id: int):
    central = crud.get_alarm_central(db, central_id)
    if not central:
        raise HTTPException(status_code=404, detail="Central não encontrada")
    return central


def _build_http_adapter(central) -> IntelbrasHTTPAdapter:
    return IntelbrasHTTPAdapter(
        ip=central.ip or "0.0.0.0",
        username="admin",
        password=central.password or "admin",
        port=80,
    )
