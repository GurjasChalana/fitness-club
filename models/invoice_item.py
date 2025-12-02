from sqlalchemy import Column, Integer, Numeric, Text, ForeignKey

from .base import Base


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    item_id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id", ondelete="CASCADE"))
    description = Column(Text)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(8, 2), nullable=False)
