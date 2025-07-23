from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Camera(Base):
    __tablename__ = "cameras"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ip_address = Column(String, unique=True, index=True)
    username = Column(String)
    password = Column(String)
    camera_type = Column(String, default="bronze")
    events = relationship("Event", back_populates="camera")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    event_type = Column(String, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"))
    camera = relationship("Camera", back_populates="events")