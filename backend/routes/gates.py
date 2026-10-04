from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.core import SessionLocal
from adapters.gate.factory import get_gate_adapter
from auth.jwt_middleware import get_current_tenant_id
import crud
import schemas

router = APIRouter(prefix="/gates", tags=["gates"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=list[schemas.Gate])
def list_gates(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.get_gates(db, tenant_id=tenant_id)


@router.post("/", response_model=schemas.Gate)
def create_gate(
    gate: schemas.GateCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.create_gate(db, gate, tenant_id=tenant_id)


@router.get("/{gate_id}", response_model=schemas.Gate)
def get_gate(gate_id: int, db: Session = Depends(get_db)):
    gate = crud.get_gate(db, gate_id)
    if not gate:
        raise HTTPException(status_code=404, detail="Portão não encontrado")
    return gate


@router.put("/{gate_id}", response_model=schemas.Gate)
def update_gate(gate_id: int, data: schemas.GateUpdate, db: Session = Depends(get_db)):
    gate = crud.update_gate(db, gate_id, data)
    if not gate:
        raise HTTPException(status_code=404, detail="Portão não encontrado")
    return gate


@router.delete("/{gate_id}")
def delete_gate(gate_id: int, db: Session = Depends(get_db)):
    if not crud.delete_gate(db, gate_id):
        raise HTTPException(status_code=404, detail="Portão não encontrado")
    return {"message": "Portão removido com sucesso"}


@router.get("/{gate_id}/status")
def get_gate_status(gate_id: int, db: Session = Depends(get_db)):
    gate = crud.get_gate(db, gate_id)
    if not gate:
        raise HTTPException(status_code=404, detail="Portão não encontrado")
    adapter = get_gate_adapter(gate)
    status = adapter.get_status()
    crud.update_gate_status(db, gate_id, status)
    return {"gate_id": gate_id, "status": status}


@router.post("/{gate_id}/trigger")
def trigger_gate(gate_id: int, db: Session = Depends(get_db)):
    gate = crud.get_gate(db, gate_id)
    if not gate:
        raise HTTPException(status_code=404, detail="Portão não encontrado")

    adapter = get_gate_adapter(gate)
    success = adapter.trigger()

    if success:
        crud.update_gate_status(db, gate_id, "moving")
        return {"message": f"Pulso enviado para {gate.name}", "success": True}

    return {
        "message": (
            f"Aviso: nenhuma interface respondeu em {gate.ip}:{gate.port}. "
            f"Verifique IP, porta e brand ({gate.brand}) do portão."
        ),
        "success": False,
    }
