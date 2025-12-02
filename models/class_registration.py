from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship

from .base import Base


class ClassRegistration(Base):
    __tablename__ = "class_registrations"
    __table_args__ = (UniqueConstraint("member_id", "class_id", name="uq_member_class"),)

    member_id = Column(Integer, ForeignKey("members.member_id", ondelete="CASCADE"), primary_key=True)
    class_id = Column(Integer, ForeignKey("group_classes.class_id", ondelete="CASCADE"), primary_key=True)
    registered_at = Column(DateTime, server_default=func.now())

    member = relationship("Member", overlaps="class_registrations")
    group_class = relationship("GroupClass", overlaps="class_registrations")
