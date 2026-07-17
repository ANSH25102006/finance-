import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Transaction(Base):
    """Represents a financial transaction (income/expense)."""

    __tablename__ = "transactions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_id = Column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    description = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    transaction_type = Column(String, nullable=False) # 'income' or 'expense'
    merchant = Column(String, nullable=True)
    confidence_score = Column(Integer, nullable=True)
    transaction_date = Column(Date, nullable=False, index=True)
    notes = Column(String, nullable=True)
    recurring = Column(Boolean, default=False, nullable=False)
    attachment_url = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} description={self.description} amount={self.amount}>"

