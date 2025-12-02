from sqlalchemy import Column, DateTime, Integer, Text, String, ForeignKey, func
from sqlalchemy.orm import relationship

from .base import Base


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    log_id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, ForeignKey("equipment.equipment_id"))
    issue_description = Column(Text)
    status = Column(String(30), default="OPEN")
    created_at = Column(DateTime, server_default=func.now())
    resolved_timestamp = Column(DateTime)
    resolution_notes = Column(Text)

    equipment = relationship("Equipment", overlaps="maintenance_logs")
