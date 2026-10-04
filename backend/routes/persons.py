import base64
import json
import os
import datetime

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.core import SessionLocal
from auth.jwt_middleware import get_current_tenant_id
import crud
import schemas

router = APIRouter(prefix="/persons", tags=["persons"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=list[schemas.Person])
def list_persons(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    return crud.get_persons(db, skip=skip, limit=limit, active_only=active_only, tenant_id=tenant_id)


@router.post("/", response_model=schemas.Person)
def create_person(
    person: schemas.PersonCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
    if person.cpf:
        existing = crud.get_person_by_cpf(db, person.cpf)
        if existing:
            raise HTTPException(status_code=400, detail="CPF já cadastrado")
    return crud.create_person(db, person, tenant_id=tenant_id)


@router.get("/cpf/{cpf}", response_model=schemas.Person)
def get_person_by_cpf(cpf: str, db: Session = Depends(get_db)):
    person = crud.get_person_by_cpf(db, cpf)
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return person


@router.get("/{person_id}", response_model=schemas.Person)
def get_person(person_id: int, db: Session = Depends(get_db)):
    person = crud.get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return person


@router.put("/{person_id}", response_model=schemas.Person)
def update_person(person_id: int, data: schemas.PersonUpdate, db: Session = Depends(get_db)):
    person = crud.update_person(db, person_id, data)
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return person


@router.delete("/{person_id}")
def deactivate_person(person_id: int, db: Session = Depends(get_db)):
    success = crud.deactivate_person(db, person_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return {"message": "Pessoa desativada com sucesso"}


class FaceEnrollRequest(BaseModel):
    image_base64: str


@router.post("/{person_id}/enroll-face", response_model=schemas.Person)
def enroll_face(person_id: int, body: FaceEnrollRequest, db: Session = Depends(get_db)):
    """
    Generate a facial embedding from a base64-encoded photo and store it
    in Person.face_encoding. Also saves the photo to face_images/.
    """
    person = crud.get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")

    raw = body.image_base64
    if "," in raw:
        raw = raw.split(",", 1)[1]

    try:
        img_bytes = base64.b64decode(raw)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except Exception:
        raise HTTPException(status_code=400, detail="Imagem base64 inválida")

    if frame is None:
        raise HTTPException(status_code=400, detail="Não foi possível decodificar a imagem")

    try:
        from ai.face_recognizer import get_embedding
        embedding = get_embedding(frame)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar IA facial: {e}")

    if embedding is None:
        raise HTTPException(status_code=422, detail="Nenhum rosto detectado na imagem")

    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"person_{person_id}_{ts}.jpg"
    photo_path = os.path.join("face_images", filename)
    cv2.imwrite(photo_path, frame)

    updated = crud.update_person(db, person_id, schemas.PersonUpdate(
        face_encoding=json.dumps(embedding.tolist()),
        photo_path=filename,
    ))
    return updated
