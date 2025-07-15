from pydantic import BaseModel
from typing import Optional, Dict, Any

class CameraBase(BaseModel):
    name: str
    ip_address: str
    level: str

class CameraCreate(CameraBase):
    pass

class Camera(CameraBase):
    id: int

    class Config:
        orm_mode = True

class Event(BaseModel):
    id: int
    camera_id: int
    timestamp: str
    event_type: str
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True