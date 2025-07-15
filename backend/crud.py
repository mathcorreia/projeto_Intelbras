from sqlalchemy.orm import Session
from database import models 
import schemas             

def get_camera(db: Session, camera_id: int):
    return db.query(models.Camera).filter(models.Camera.id == camera_id).first()

def get_cameras(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Camera).offset(skip).limit(limit).all()

def create_camera(db: Session, camera: schemas.CameraCreate):
    db_camera = models.Camera(
        name=camera.name, 
        ip_address=camera.ip_address, 
        level=camera.level
    )
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera

def create_event(db: Session, event_data: dict, camera_id: int):
    db_event = models.Event(
        camera_id=camera_id,
        timestamp=event_data.get("timestamp"),
        event_type=event_data.get("type"),
        metadata=event_data.get("attributes")
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event