from pydantic import BaseModel
from typing import Optional
import datetime


# ============================================================
# CÂMERAS E EVENTOS
# ============================================================

class EventBase(BaseModel):
    event_type: str
    event_data: Optional[str] = None
    face_image_path: Optional[str] = None

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    camera_id: int
    timestamp: datetime.datetime
    class Config:
        from_attributes = True


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


# ============================================================
# PESSOAS
# ============================================================

class PersonBase(BaseModel):
    name: str
    cpf: Optional[str] = None
    department: Optional[str] = None
    access_level: str = "standard"
    photo_path: Optional[str] = None

class PersonCreate(PersonBase):
    face_encoding: Optional[str] = None  # JSON string do embedding facial

class PersonUpdate(PersonBase):
    face_encoding: Optional[str] = None

class Person(PersonBase):
    id: int
    is_active: bool
    created_at: datetime.datetime
    class Config:
        from_attributes = True


# ============================================================
# VISITANTES
# ============================================================

class VisitorBase(BaseModel):
    name: str
    cpf: Optional[str] = None
    host: str
    destination: Optional[str] = None
    valid_from: Optional[datetime.datetime] = None
    valid_until: datetime.datetime
    photo_path: Optional[str] = None
    notes: Optional[str] = None
    person_id: Optional[int] = None

class VisitorCreate(VisitorBase):
    pass

class VisitorUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    destination: Optional[str] = None
    valid_until: Optional[datetime.datetime] = None
    notes: Optional[str] = None

class VisitorStatusUpdate(BaseModel):
    status: str  # pending, approved, denied, expired

class Visitor(VisitorBase):
    id: int
    status: str
    created_at: datetime.datetime
    class Config:
        from_attributes = True


# ============================================================
# ALARMES
# ============================================================

class AlarmZoneBase(BaseModel):
    zone_number: int
    name: str
    zone_type: Optional[str] = None
    is_bypassed: bool = False

class AlarmZoneCreate(AlarmZoneBase):
    central_id: int

class AlarmZoneUpdate(BaseModel):
    name: Optional[str] = None
    zone_type: Optional[str] = None
    is_bypassed: Optional[bool] = None
    status: Optional[str] = None

class AlarmZone(AlarmZoneBase):
    id: int
    central_id: int
    status: str
    class Config:
        from_attributes = True


class AlarmCentralBase(BaseModel):
    name: str
    model: Optional[str] = None
    ip: Optional[str] = None
    port: int = 9009
    protocol: str = "contact_id"

class AlarmCentralCreate(AlarmCentralBase):
    password: Optional[str] = None

class AlarmCentralUpdate(AlarmCentralBase):
    password: Optional[str] = None

class AlarmCentral(AlarmCentralBase):
    id: int
    is_active: bool
    zones: list[AlarmZone] = []
    class Config:
        from_attributes = True


class AlarmEventCreate(BaseModel):
    central_id: int
    zone_id: Optional[int] = None
    event_type: str
    qualifier: Optional[str] = None
    raw_data: Optional[str] = None

class AlarmEvent(AlarmEventCreate):
    id: int
    timestamp: datetime.datetime
    class Config:
        from_attributes = True


# ============================================================
# CONTROLE DE ACESSO
# ============================================================

class AccessDeviceBase(BaseModel):
    name: str
    device_type: str
    ip: Optional[str] = None
    port: int = 80
    location: Optional[str] = None
    username: Optional[str] = None
    camera_id: Optional[int] = None
    gate_id: Optional[int] = None
    time_rules: Optional[str] = None        # JSON: {"allowed_days":[0..6],"start_time":"HH:MM","end_time":"HH:MM"}
    min_access_level: Optional[str] = None  # restricted | standard | admin

class AccessDeviceCreate(AccessDeviceBase):
    password: Optional[str] = None

class AccessDeviceUpdate(AccessDeviceBase):
    password: Optional[str] = None

class AccessDevice(AccessDeviceBase):
    id: int
    is_active: bool
    class Config:
        from_attributes = True


class AccessLogCreate(BaseModel):
    person_id: Optional[int] = None
    device_id: Optional[int] = None
    result: str
    method: Optional[str] = None
    confidence: Optional[float] = None
    photo_path: Optional[str] = None
    direction: Optional[str] = None
    notes: Optional[str] = None

class AccessLog(AccessLogCreate):
    id: int
    timestamp: datetime.datetime
    class Config:
        from_attributes = True


# ============================================================
# PORTÕES
# ============================================================

class GateBase(BaseModel):
    name: str
    brand: Optional[str] = None
    ip: str
    port: int = 80
    pulse_time: int = 1
    location: Optional[str] = None
    username: Optional[str] = None

class GateCreate(GateBase):
    password: Optional[str] = None

class GateUpdate(GateBase):
    password: Optional[str] = None

class Gate(GateBase):
    id: int
    is_active: bool
    status: str
    class Config:
        from_attributes = True
