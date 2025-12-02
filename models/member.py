from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship

from .base import Base


class Member(Base):
    __tablename__ = "members"

    member_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(String(20))
    phone = Column(String(30))

    goals = relationship("FitnessGoal", cascade="all, delete-orphan")
    metrics = relationship("HealthMetric", cascade="all, delete-orphan")
    pt_sessions = relationship("PersonalTrainingSession", cascade="all, delete-orphan")
    class_registrations = relationship("ClassRegistration", cascade="all, delete-orphan")
    invoices = relationship("Invoice", cascade="all, delete-orphan")
