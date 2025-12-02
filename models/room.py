from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(Integer, primary_key=True)
    room_name = Column(String(50), unique=True, nullable=False)
    capacity = Column(Integer, nullable=False)

    classes = relationship("GroupClass", cascade="all, delete-orphan")
    pt_sessions = relationship("PersonalTrainingSession", cascade="all, delete-orphan")
    equipment = relationship("Equipment", cascade="all, delete-orphan")
