from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .database import Base

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ip_address = Column(String, unique=True, index=True)
    level = Column(String, default="bronze") # 'bronze', 'silver', 'gold'
    
    events = relationship("Event", back_populates="camera")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"))
    timestamp = Column(String)
    event_type = Column(String)
    snapshot_path = Column(String, nullable=True)
    metadata = Column(JSONB, nullable=True)

    camera = relationship("Camera", back_populates="events")