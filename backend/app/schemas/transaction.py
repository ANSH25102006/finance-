from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal


class TransactionBase(BaseModel):
    account_id: UUID
    category_id: Optional[UUID] = None
    description: str
    amount: Decimal = Field(gt=Decimal('0.00'))
    transaction_type: str  # 'income' or 'expense' or 'transfer'
    merchant: Optional[str] = None
    transaction_date: date
    notes: Optional[str] = None
    recurring: bool = False
    attachment_url: Optional[str] = None

    @field_validator('transaction_date')
    @classmethod
    def validate_date_not_in_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Transaction date cannot be in the future.")
        return v

    @field_validator('transaction_type')
    @classmethod
    def validate_transaction_type(cls, v: str) -> str:
        valid_types = {"income", "expense", "transfer"}
        if v not in valid_types:
            raise ValueError("Transaction type must be 'income', 'expense', or 'transfer'.")
        return v


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    account_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=Decimal('0.00'))
    transaction_type: Optional[str] = None
    merchant: Optional[str] = None
    transaction_date: Optional[date] = None
    notes: Optional[str] = None
    recurring: Optional[bool] = None
    attachment_url: Optional[str] = None

    @field_validator('transaction_date')
    @classmethod
    def validate_date_not_in_future(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("Transaction date cannot be in the future.")
        return v

    @field_validator('transaction_type')
    @classmethod
    def validate_transaction_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_types = {"income", "expense", "transfer"}
            if v not in valid_types:
                raise ValueError("Transaction type must be 'income', 'expense', or 'transfer'.")
        return v


class TransactionResponse(TransactionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('amount')
    def serialize_amount(self, v: Decimal, _info) -> float:
        """Serialize Decimal amount as float so JSON contains a number not a string."""
        return float(v)


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    pages: int
    limit: int

