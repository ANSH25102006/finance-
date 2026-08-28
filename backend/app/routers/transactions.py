from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_
from typing import Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
import math

from app.database import get_db
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
)
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def validate_account_and_category(
    db: Session,
    user_id: UUID,
    account_id: UUID,
    category_id: Optional[UUID] = None,
):
    """Verify that the account and category belong to the authenticated user."""
    # Verify account
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.user_id == user_id)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account not found or access denied.",
        )

    # Verify category if provided
    if category_id:
        category = (
            db.query(Category)
            .filter(
                Category.id == category_id,
                or_(Category.user_id == user_id, Category.user_id.is_(None)),
            )
            .first()
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or access denied.",
            )


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new transaction with ownership validations."""
    validate_account_and_category(
        db,
        current_user.id,
        transaction_in.account_id,
        transaction_in.category_id,
    )

    transaction = Transaction(**transaction_in.model_dump(), user_id=current_user.id)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/", response_model=TransactionListResponse)
def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    account_id: Optional[UUID] = None,
    category_id: Optional[UUID] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    recurring: Optional[bool] = None,
    sort_by: str = Query("transaction_date"),
    sort_order: str = Query("desc"),
):
    """Retrieve all transactions with robust filtering, sorting, and pagination."""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    # Filtering
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)
    if recurring is not None:
        query = query.filter(Transaction.recurring.is_(recurring))

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Transaction.description.ilike(search_filter),
                Transaction.merchant.ilike(search_filter),
                Transaction.notes.ilike(search_filter),
            )
        )

    # Sorting
    valid_sort_fields = {"transaction_date", "amount", "created_at"}
    if sort_by not in valid_sort_fields:
        sort_by = "transaction_date"

    sort_col = getattr(Transaction, sort_by)
    if sort_order == "asc":
        query = query.order_by(asc(sort_col), asc(Transaction.created_at))
    else:
        query = query.order_by(desc(sort_col), desc(Transaction.created_at))

    # Pagination
    total = query.count()
    pages = math.ceil(total / limit) if limit > 0 else 0
    skip = (page - 1) * limit
    items = query.offset(skip).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
        "limit": limit,
    }


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a specific transaction by ID."""
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: UUID,
    transaction_in: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a specific transaction with validation of modified account/category."""
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    # Validate new account or category if they are being updated
    updated_account_id = transaction_in.account_id or transaction.account_id
    updated_category_id = transaction_in.category_id or transaction.category_id
    
    validate_account_and_category(
        db,
        current_user.id,
        updated_account_id,
        updated_category_id,
    )

    update_data = transaction_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(transaction, key, value)

    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a specific transaction."""
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    db.delete(transaction)
    db.commit()
    return None

