"""Card invoices repository."""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.card_invoice import CardInvoice, InvoiceStatus
from app.repositories.base_repo import BaseRepository


class CardInvoicesRepository(BaseRepository[CardInvoice]):
    """Repository for CardInvoice operations."""

    def __init__(self, db: Session):
        super().__init__(db, CardInvoice)

    def get_invoice_by_month(self, card_id: str, reference_month: str) -> CardInvoice:
        """Get invoice for a specific card and month."""
        return self.db.query(CardInvoice).filter(
            CardInvoice.card_id == card_id,
            CardInvoice.reference_month == reference_month,
        ).first()

    def list_pending_invoices(self, card_id: str) -> List[CardInvoice]:
        """List pending invoices for a card."""
        return self.db.query(CardInvoice).filter(
            CardInvoice.card_id == card_id,
            CardInvoice.status == InvoiceStatus.PENDING,
        ).order_by(CardInvoice.reference_month.desc()).all()

    def list_paid_invoices(self, card_id: str, skip: int = 0, limit: int = 50):
        """List paid invoices for a card."""
        return self.db.query(CardInvoice).filter(
            CardInvoice.card_id == card_id,
            CardInvoice.status == InvoiceStatus.PAID,
        ).order_by(
            CardInvoice.reference_month.desc()
        ).offset(skip).limit(limit).all()

    def mark_as_paid(self, invoice_id: str) -> CardInvoice:
        """Mark invoice as paid."""
        invoice = self.db.query(CardInvoice).filter(CardInvoice.id == invoice_id).first()
        if invoice:
            invoice.status = InvoiceStatus.PAID
            self.db.commit()
            self.db.refresh(invoice)
        return invoice

    def mark_as_overdue(self, invoice_id: str) -> CardInvoice:
        """Mark invoice as overdue."""
        invoice = self.db.query(CardInvoice).filter(CardInvoice.id == invoice_id).first()
        if invoice:
            invoice.status = InvoiceStatus.OVERDUE
            self.db.commit()
            self.db.refresh(invoice)
        return invoice

    def get_total_pending_balance(self, card_id: str) -> float:
        """Get total balance of pending invoices."""
        total = self.db.query(
            func.sum(CardInvoice.total_amount - CardInvoice.paid_amount)
        ).filter(
            CardInvoice.card_id == card_id,
            CardInvoice.status == InvoiceStatus.PENDING,
        ).scalar() or 0.0

        return max(0.0, total)
