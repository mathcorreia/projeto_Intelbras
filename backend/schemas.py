from pydantic import BaseModel
from typing import Optional
import datetime

# --- Esquema para Eventos ---
class EventBase(BaseModel):
    event_type: str
    event_data: Optional[str] = None # <-- RENOMEADO
    face_image_path: Optional[str] = None
class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    camera_id: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

# --- Esquema para Câmeras ---
class CameraBase(BaseModel):
    name: str
    ip_address: str
    username: str
    camera_type: str

class CameraCreate(CameraBase):
    password: str

class Camera(CameraBase):
    id: int
    events: list[Event] = []

    class Config:
        from_attributes = True