from datetime import datetime
from sqlalchemy import Column, Date, Integer, Numeric, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.member_id"))
    issue_date = Column(Date, default=datetime.utcnow)
    due_date = Column(Date)
    total_amount = Column(Numeric(8, 2), nullable=False, default=0)
    status = Column(String(30), default="UNPAID")
    notes = Column(Text)

    member = relationship("Member", overlaps="invoices")
    items = relationship("InvoiceItem", cascade="all, delete-orphan", overlaps="payments")
    payments = relationship("Payment", cascade="all, delete-orphan", overlaps="items")
