from sqlalchemy.orm import Session
from .database import models
from . import schemas

def get_camera(db: Session, camera_id: int):
    return db.query(models.Camera).filter(models.Camera.id == camera_id).first()

def get_cameras(db: Session):
    return db.query(models.Camera).all()

def create_camera(db: Session, camera: schemas.CameraCreate):
    db_camera = models.Camera(**camera.model_dump())
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera

def get_events_for_camera(db: Session, camera_id: int):
    return db.query(models.Event).filter(models.Event.camera_id == camera_id).order_by(models.Event.timestamp.desc()).all()

def create_event(db: Session, event: schemas.EventCreate, camera_id: int):
    # Esta linha já funciona para os novos campos, pois eles estão no esquema EventCreate
    db_event = models.Event(**event.model_dump(), camera_id=camera_id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event