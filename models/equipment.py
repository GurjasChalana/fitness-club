from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Equipment(Base):
    __tablename__ = "equipment"

    equipment_id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.room_id"))
    equipment_name = Column(String(100), nullable=False)
    status = Column(String(30), default="OPERATIONAL")

    room = relationship("Room", overlaps="equipment")
    maintenance_logs = relationship("MaintenanceLog", cascade="all, delete-orphan", overlaps="maintenance_logs")
