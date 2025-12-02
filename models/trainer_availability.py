from sqlalchemy import CheckConstraint, Column, DateTime, Integer, Text, ForeignKey

from .base import Base


class TrainerAvailability(Base):
    __tablename__ = "trainer_availability"
    __table_args__ = (CheckConstraint("start_time < end_time"),)

    availability_id = Column(Integer, primary_key=True)
    trainer_id = Column(Integer, ForeignKey("trainers.trainer_id", ondelete="CASCADE"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    notes = Column(Text)
