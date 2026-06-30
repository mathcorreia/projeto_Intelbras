from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.core import SessionLocal
from auth.jwt_middleware import get_current_tenant_id
import crud
import schemas

router = APIRouter(prefix="/visitors", tags=["visitors"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=list[schemas.Visitor])
def list_visitors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.get_visitors(db, skip=skip, limit=limit, tenant_id=tenant_id)


@router.get("/active", response_model=list[schemas.Visitor])
def list_active_visitors(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.get_active_visitors(db, tenant_id=tenant_id)


@router.post("/", response_model=schemas.Visitor)
def create_visitor(
    visitor: schemas.VisitorCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.create_visitor(db, visitor, tenant_id=tenant_id)


@router.get("/{visitor_id}", response_model=schemas.Visitor)
def get_visitor(visitor_id: int, db: Session = Depends(get_db)):
    visitor = crud.get_visitor(db, visitor_id)
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitante não encontrado")
    return visitor


@router.put("/{visitor_id}", response_model=schemas.Visitor)
def update_visitor(visitor_id: int, data: schemas.VisitorUpdate, db: Session = Depends(get_db)):
    visitor = crud.update_visitor(db, visitor_id, data)
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitante não encontrado")
    return visitor


@router.patch("/{visitor_id}/status", response_model=schemas.Visitor)
def update_visitor_status(visitor_id: int, body: schemas.VisitorStatusUpdate, db: Session = Depends(get_db)):
    valid_statuses = {"pending", "approved", "denied", "expired"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status inválido. Use: {valid_statuses}")
    visitor = crud.update_visitor_status(db, visitor_id, body.status)
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitante não encontrado")
    return visitor
