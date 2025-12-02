from sqlalchemy import Column, DateTime, Integer, Numeric, String, ForeignKey, func
from sqlalchemy.orm import relationship

from .base import Base


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id"))
    amount = Column(Numeric(8, 2), nullable=False)
    payment_method = Column(String(30))
    status = Column(String(30), default="SUCCESS")
    payment_date = Column(DateTime, server_default=func.now())
    reference = Column(String(120))

    invoice = relationship("Invoice", overlaps="payments,items")
