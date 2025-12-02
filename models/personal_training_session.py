from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class PersonalTrainingSession(Base):
    __tablename__ = "personal_training_sessions"
    __table_args__ = (CheckConstraint("start_time < end_time"),)

    session_id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.member_id", ondelete="CASCADE"))
    trainer_id = Column(Integer, ForeignKey("trainers.trainer_id", ondelete="CASCADE"))
    room_id = Column(Integer, ForeignKey("rooms.room_id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    session_type = Column(String(50))
    notes = Column(Text)
    status = Column(String(20), default="SCHEDULED")

    member = relationship("Member", overlaps="pt_sessions")
    trainer = relationship("Trainer", overlaps="pt_sessions")
    room = relationship("Room", overlaps="pt_sessions")
