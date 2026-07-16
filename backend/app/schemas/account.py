from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class AccountBase(BaseModel):
    name: str
    balance: float = 0.0
    currency: str = "INR"
    icon: Optional[str] = None
    color: Optional[str] = None
    institution: Optional[str] = None
    archived: bool = False


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    institution: Optional[str] = None
    archived: Optional[bool] = None


class AccountResponse(AccountBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
