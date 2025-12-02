from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class GroupClass(Base):
    __tablename__ = "group_classes"

    class_id = Column(Integer, primary_key=True)
    class_name = Column(String(100), nullable=False)
    trainer_id = Column(Integer, ForeignKey("trainers.trainer_id"))
    room_id = Column(Integer, ForeignKey("rooms.room_id"))
    class_time = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(String(20), default="SCHEDULED")

    trainer = relationship("Trainer", overlaps="classes")
    room = relationship("Room", overlaps="classes")
