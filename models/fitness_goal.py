from sqlalchemy import Boolean, Column, Integer, Numeric, String, ForeignKey

from .base import Base


class FitnessGoal(Base):
    __tablename__ = "fitness_goals"

    goal_id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.member_id", ondelete="CASCADE"))
    goal_type = Column(String(50), nullable=False)
    target_value = Column(Numeric(6, 2), nullable=False)
    is_active = Column(Boolean, default=True)
