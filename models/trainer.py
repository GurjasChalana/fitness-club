from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Trainer(Base):
    __tablename__ = "trainers"

    trainer_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    certification = Column(String(100))

    availability = relationship("TrainerAvailability", cascade="all, delete-orphan")
    pt_sessions = relationship("PersonalTrainingSession", cascade="all, delete-orphan")
    classes = relationship("GroupClass", cascade="all, delete-orphan")
