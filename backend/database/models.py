from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, TEXT, Boolean, Float
from sqlalchemy.orm import relationship
import datetime
from .core import Base


# --- MULTITENANCY (Fase 7) ---
# tenant_id = 1 é o tenant padrão (single-tenant / dev).
# Quando o Java backendPerm estiver ativo, o JWT middleware injeta o tenant_id real em cada request.
# Nenhuma query deve cruzar tenant_id diferente.

class Camera(Base):
    __tablename__ = "cameras"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, default=1, nullable=False, index=True)
    name = Column(String, index=True)
    ip_address = Column(String, unique=True, index=True)
    username = Column(String)
    password = Column(String)
    camera_type = Column(String, default="onvif")
    events = relationship("Event", back_populates="camera")


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, default=1, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    event_type = Column(String, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"))
    camera = relationship("Camera", back_populates="events")
    event_data = Column(TEXT, nullable=True)
    face_image_path = Column(String, nullable=True)


# --- PESSOAS E VISITANTES ---

class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, default=1, nullable=False, index=True)
    name = Column(String, index=True)
    cpf = Column(String, unique=True, index=True, nullable=True)
    department = Column(String, nullable=True)
    access_level = Column(String, default="standard")  # standard, admin, restricted
    face_encoding = Column(TEXT, nullable=True)         # JSON array de floats (embedding facial)
    photo_path = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    access_logs = relationship("AccessLog", back_populates="person")
    visitors = relationship("Visitor", back_populates="person")


class Visitor(Base):
    __tablename__ = "visitors"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, default=1, nullable=False, index=True)
    name = Column(String, index=True)
    cpf = Column(String, nullable=True)
    host = Column(String)                               # responsável/anfitrião
    destination = Column(String, nullable=True)         # destino dentro do local
    valid_from = Column(DateTime, default=datetime.datetime.utcnow)
    valid_until = Column(DateTime)
    status = Column(String, default="pending")          # pending, approved, denied, expired
    photo_path = Column(String, nullable=True)
    notes = Column(TEXT, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)  # se já tiver cadastro

    person = relationship("Person", back_populates="visitors")


# --- ALARMES ---

class AlarmCentral(Base):
    __tablename__ = "alarm_centrals"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, default=1, nullable=False, index=True)
    name = Column(String, index=True)
    model = Column(String, nullable=True)               # AMT 2018 EG, AMT 8000, etc.
    ip = Column(String, nullable=True)
    port = Column(Integer, default=9009)
    password = Column(String, nullable=True)
    protocol = Column(String, default="contact_id")
    is_active = Column(Boolean, default=True)

    zones = relationship("AlarmZone", back_populates="central", cascade="all, delete-orphan")
    events = relationship("AlarmEvent", back_populates="central", cascade="all, delete-orphan")


class AlarmZone(Base):
    __tablename__ = "alarm_zones"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, default=1, nullable=False, index=True)
    central_id = Column(Integer, ForeignKey("alarm_centrals.id"))
    zone_number = Column(Integer)
    name = Column(String)
    zone_type = Column(String, nullable=True)           # infra, magnetic, vibration, smoke, etc.
    is_bypassed = Column(Boolean, default=False)
    status = Column(String, default="normal")           # normal, open, alarm, fault

    central = relationship("AlarmCentral", back_populates="zones")
    events = relationship("AlarmEvent", back_populates="zone")


class AlarmEvent(Base):
    __tablename__ = "alarm_events"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, default=1, nullable=False, index=True)
    central_id = Column(Integer, ForeignKey("alarm_centrals.id"))
    zone_id = Column(Integer, ForeignKey("alarm_zones.id"), nullable=True)
    event_type = Column(String, index=True)             # alarm, restore, arm, disarm, bypass, tamper
    qualifier = Column(String, nullable=True)           # Contact ID qualifier (E=evento, R=restore)
    raw_data = Column(String, nullable=True)            # hex bruto recebido via TCP
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    central = relationship("AlarmCentral", back_populates="events")
    zone = relationship("AlarmZone", back_populates="events")


# --- CONTROLE DE ACESSO ---

class AccessDevice(Base):
    __tablename__ = "access_devices"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, default=1, nullable=False, index=True)
    name = Column(String)
    device_type = Column(String)                        # catraca, leitor_rfid, controle_acesso, cancela
    ip = Column(String, nullable=True)
    port = Column(Integer, default=80)
    location = Column(String, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # Fase 4: vínculo com câmera (fonte do reconhecimento facial) e portão (atuador físico)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)
    gate_id = Column(Integer, ForeignKey("gates.id"), nullable=True)

    # Regras de horário: {"allowed_days": [0..6], "start_time": "08:00", "end_time": "18:00"}
    time_rules = Column(TEXT, nullable=True)
    min_access_level = Column(String, nullable=True)    # restricted | standard | admin

    access_logs = relationship("AccessLog", back_populates="device")


class AccessLog(Base):
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, default=1, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    device_id = Column(Integer, ForeignKey("access_devices.id"), nullable=True)
    result = Column(String)                             # granted, denied, unknown
    method = Column(String, nullable=True)              # facial, rfid, pin, manual
    confidence = Column(Float, nullable=True)           # confiança do reconhecimento facial (0-100)
    photo_path = Column(String, nullable=True)          # foto capturada no momento do acesso
    direction = Column(String, nullable=True)           # in, out
    notes = Column(TEXT, nullable=True)

    person = relationship("Person", back_populates="access_logs")
    device = relationship("AccessDevice", back_populates="access_logs")


# --- PORTÕES ---

class Gate(Base):
    __tablename__ = "gates"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, default=1, nullable=False, index=True)
    name = Column(String)
    brand = Column(String, nullable=True)               # PPA, Intelbras, etc.
    ip = Column(String)
    port = Column(Integer, default=80)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    pulse_time = Column(Integer, default=1)             # duração do pulso em segundos
    location = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    status = Column(String, default="unknown")          # open, closed, moving, unknown
