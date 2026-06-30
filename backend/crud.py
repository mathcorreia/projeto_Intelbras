from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import models
import schemas


# ============================================================
# CÂMERAS
# ============================================================

def get_camera(db: Session, camera_id: int):
    return db.query(models.Camera).filter(models.Camera.id == camera_id).first()

def get_cameras(db: Session, tenant_id: int = 1):
    return db.query(models.Camera).filter(models.Camera.tenant_id == tenant_id).all()

def create_camera(db: Session, camera: schemas.CameraCreate, tenant_id: int = 1):
    db_camera = models.Camera(**camera.model_dump())
    db_camera.tenant_id = tenant_id
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera

def delete_camera(db: Session, camera_id: int):
    db_camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if db_camera:
        db.query(models.Event).filter(models.Event.camera_id == camera_id).delete()
        db.delete(db_camera)
        db.commit()
        return True
    return False

def update_camera(db: Session, camera_id: int, camera_data: schemas.CameraCreate):
    db_camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if db_camera:
        for key, value in camera_data.model_dump().items():
            setattr(db_camera, key, value)
        db.commit()
        db.refresh(db_camera)
        return db_camera
    return None

def get_events_for_camera(db: Session, camera_id: int):
    return db.query(models.Event).filter(models.Event.camera_id == camera_id).order_by(desc(models.Event.timestamp)).all()

def create_event(db: Session, event: schemas.EventCreate, camera_id: int, tenant_id: int = 1):
    db_event = models.Event(**event.model_dump(), camera_id=camera_id)
    db_event.tenant_id = tenant_id
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


# ============================================================
# PESSOAS
# ============================================================

def get_persons(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False, tenant_id: int = 1):
    q = db.query(models.Person).filter(models.Person.tenant_id == tenant_id)
    if active_only:
        q = q.filter(models.Person.is_active == True)
    return q.offset(skip).limit(limit).all()

def get_person(db: Session, person_id: int):
    return db.query(models.Person).filter(models.Person.id == person_id).first()

def get_person_by_cpf(db: Session, cpf: str):
    return db.query(models.Person).filter(models.Person.cpf == cpf).first()

def create_person(db: Session, person: schemas.PersonCreate, tenant_id: int = 1):
    db_person = models.Person(**person.model_dump())
    db_person.tenant_id = tenant_id
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person

def update_person(db: Session, person_id: int, data: schemas.PersonUpdate):
    db_person = db.query(models.Person).filter(models.Person.id == person_id).first()
    if db_person:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(db_person, key, value)
        db.commit()
        db.refresh(db_person)
        return db_person
    return None

def deactivate_person(db: Session, person_id: int):
    db_person = db.query(models.Person).filter(models.Person.id == person_id).first()
    if db_person:
        db_person.is_active = False
        db.commit()
        return True
    return False

def get_persons_with_face_encoding(db: Session, tenant_id: int = 1):
    return db.query(models.Person).filter(
        models.Person.tenant_id == tenant_id,
        models.Person.face_encoding != None,
        models.Person.is_active == True
    ).all()


# ============================================================
# VISITANTES
# ============================================================

def get_visitors(db: Session, skip: int = 0, limit: int = 100, tenant_id: int = 1):
    return (
        db.query(models.Visitor)
        .filter(models.Visitor.tenant_id == tenant_id)
        .order_by(desc(models.Visitor.created_at))
        .offset(skip).limit(limit).all()
    )

def get_visitor(db: Session, visitor_id: int):
    return db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()

def get_active_visitors(db: Session, tenant_id: int = 1):
    import datetime
    now = datetime.datetime.utcnow()
    return db.query(models.Visitor).filter(
        models.Visitor.tenant_id == tenant_id,
        models.Visitor.status == "approved",
        models.Visitor.valid_until >= now
    ).all()

def create_visitor(db: Session, visitor: schemas.VisitorCreate, tenant_id: int = 1):
    db_visitor = models.Visitor(**visitor.model_dump())
    db_visitor.tenant_id = tenant_id
    db.add(db_visitor)
    db.commit()
    db.refresh(db_visitor)
    return db_visitor

def update_visitor(db: Session, visitor_id: int, data: schemas.VisitorUpdate):
    db_visitor = db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
    if db_visitor:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(db_visitor, key, value)
        db.commit()
        db.refresh(db_visitor)
        return db_visitor
    return None

def update_visitor_status(db: Session, visitor_id: int, status: str):
    db_visitor = db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
    if db_visitor:
        db_visitor.status = status
        db.commit()
        db.refresh(db_visitor)
        return db_visitor
    return None


# ============================================================
# ALARMES
# ============================================================

def get_alarm_centrals(db: Session, tenant_id: int = 1):
    return db.query(models.AlarmCentral).filter(models.AlarmCentral.tenant_id == tenant_id).all()

def get_alarm_central(db: Session, central_id: int):
    return db.query(models.AlarmCentral).filter(models.AlarmCentral.id == central_id).first()

def create_alarm_central(db: Session, central: schemas.AlarmCentralCreate, tenant_id: int = 1):
    db_central = models.AlarmCentral(**central.model_dump())
    db_central.tenant_id = tenant_id
    db.add(db_central)
    db.commit()
    db.refresh(db_central)
    return db_central

def update_alarm_central(db: Session, central_id: int, data: schemas.AlarmCentralUpdate):
    db_central = db.query(models.AlarmCentral).filter(models.AlarmCentral.id == central_id).first()
    if db_central:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(db_central, key, value)
        db.commit()
        db.refresh(db_central)
        return db_central
    return None

def delete_alarm_central(db: Session, central_id: int):
    db_central = db.query(models.AlarmCentral).filter(models.AlarmCentral.id == central_id).first()
    if db_central:
        db.delete(db_central)
        db.commit()
        return True
    return False

def get_alarm_zones(db: Session, central_id: int, tenant_id: int = 1):
    return (
        db.query(models.AlarmZone)
        .filter(
            models.AlarmZone.central_id == central_id,
            models.AlarmZone.tenant_id == tenant_id,
        )
        .order_by(models.AlarmZone.zone_number)
        .all()
    )

def get_alarm_zone(db: Session, zone_id: int):
    return db.query(models.AlarmZone).filter(models.AlarmZone.id == zone_id).first()

def create_alarm_zone(db: Session, zone: schemas.AlarmZoneCreate, tenant_id: int = 1):
    db_zone = models.AlarmZone(**zone.model_dump())
    db_zone.tenant_id = tenant_id
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

def update_alarm_zone(db: Session, zone_id: int, data: schemas.AlarmZoneUpdate):
    db_zone = db.query(models.AlarmZone).filter(models.AlarmZone.id == zone_id).first()
    if db_zone:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(db_zone, key, value)
        db.commit()
        db.refresh(db_zone)
        return db_zone
    return None

def get_alarm_events(db: Session, central_id: int = None, tenant_id: int = 1, limit: int = 100):
    q = db.query(models.AlarmEvent).filter(models.AlarmEvent.tenant_id == tenant_id)
    if central_id:
        q = q.filter(models.AlarmEvent.central_id == central_id)
    return q.order_by(desc(models.AlarmEvent.timestamp)).limit(limit).all()

def create_alarm_event(db: Session, event: schemas.AlarmEventCreate, tenant_id: int = 1):
    db_event = models.AlarmEvent(**event.model_dump())
    db_event.tenant_id = tenant_id
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    # Notify Java WebSocket broker (fire-and-forget)
    try:
        from broker import notify_broker
        notify_broker("alarm", {
            "central_id": db_event.central_id,
            "zone_id": db_event.zone_id,
            "event_type": db_event.event_type,
            "qualifier": db_event.qualifier,
        }, tenant_id=tenant_id)
    except Exception:
        pass
    return db_event


# ============================================================
# CONTROLE DE ACESSO
# ============================================================

def get_access_devices(db: Session, tenant_id: int = 1):
    return db.query(models.AccessDevice).filter(models.AccessDevice.tenant_id == tenant_id).all()

def get_access_device(db: Session, device_id: int):
    return db.query(models.AccessDevice).filter(models.AccessDevice.id == device_id).first()

def get_access_device_by_camera(db: Session, camera_id: int):
    return (
        db.query(models.AccessDevice)
        .filter(models.AccessDevice.camera_id == camera_id, models.AccessDevice.is_active == True)
        .first()
    )

def get_unknown_face_events(db: Session, after_id: int = 0, tenant_id: int = 1, limit: int = 50):
    return (
        db.query(models.Event)
        .filter(
            models.Event.tenant_id == tenant_id,
            models.Event.id > after_id,
            models.Event.event_type.in_(["unknown_face", "visitor_detected"]),
        )
        .order_by(models.Event.timestamp.desc())
        .limit(limit)
        .all()
    )

def create_access_device(db: Session, device: schemas.AccessDeviceCreate, tenant_id: int = 1):
    db_device = models.AccessDevice(**device.model_dump())
    db_device.tenant_id = tenant_id
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

def update_access_device(db: Session, device_id: int, data: schemas.AccessDeviceUpdate):
    db_device = db.query(models.AccessDevice).filter(models.AccessDevice.id == device_id).first()
    if db_device:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(db_device, key, value)
        db.commit()
        db.refresh(db_device)
        return db_device
    return None

def delete_access_device(db: Session, device_id: int):
    db_device = db.query(models.AccessDevice).filter(models.AccessDevice.id == device_id).first()
    if db_device:
        db.delete(db_device)
        db.commit()
        return True
    return False

def get_access_logs(db: Session, person_id: int = None, device_id: int = None, tenant_id: int = 1, limit: int = 100):
    q = db.query(models.AccessLog).filter(models.AccessLog.tenant_id == tenant_id)
    if person_id:
        q = q.filter(models.AccessLog.person_id == person_id)
    if device_id:
        q = q.filter(models.AccessLog.device_id == device_id)
    return q.order_by(desc(models.AccessLog.timestamp)).limit(limit).all()

def create_access_log(db: Session, log: schemas.AccessLogCreate, tenant_id: int = 1):
    db_log = models.AccessLog(**log.model_dump())
    db_log.tenant_id = tenant_id
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


# ============================================================
# PORTÕES
# ============================================================

def get_gates(db: Session, tenant_id: int = 1):
    return db.query(models.Gate).filter(models.Gate.tenant_id == tenant_id).all()

def get_gate(db: Session, gate_id: int):
    return db.query(models.Gate).filter(models.Gate.id == gate_id).first()

def create_gate(db: Session, gate: schemas.GateCreate, tenant_id: int = 1):
    db_gate = models.Gate(**gate.model_dump())
    db_gate.tenant_id = tenant_id
    db.add(db_gate)
    db.commit()
    db.refresh(db_gate)
    return db_gate

def update_gate(db: Session, gate_id: int, data: schemas.GateUpdate):
    db_gate = db.query(models.Gate).filter(models.Gate.id == gate_id).first()
    if db_gate:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(db_gate, key, value)
        db.commit()
        db.refresh(db_gate)
        return db_gate
    return None

def delete_gate(db: Session, gate_id: int):
    db_gate = db.query(models.Gate).filter(models.Gate.id == gate_id).first()
    if db_gate:
        db.delete(db_gate)
        db.commit()
        return True
    return False

def update_gate_status(db: Session, gate_id: int, status: str):
    db_gate = db.query(models.Gate).filter(models.Gate.id == gate_id).first()
    if db_gate:
        db_gate.status = status
        db.commit()
        return db_gate
    return None
