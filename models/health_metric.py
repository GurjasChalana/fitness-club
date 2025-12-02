from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, func

from .base import Base


class HealthMetric(Base):
    __tablename__ = "health_metrics"

    metric_id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.member_id", ondelete="CASCADE"))
    weight = Column(Numeric(5, 2))
    heart_rate = Column(Integer)
    body_fat = Column(Numeric(5, 2))
    recorded_at = Column(DateTime, server_default=func.now())
