from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new custom category for the user."""
    # Check for duplicate name
    existing = db.query(Category).filter(
        Category.name.ilike(category_in.name),
        or_(Category.user_id == current_user.id, Category.user_id.is_(None))
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    category = Category(**category_in.model_dump(), user_id=current_user.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    type: str = None,
):
    """Retrieve all categories (both system and user-specific)."""
    query = db.query(Category).filter(
        or_(Category.user_id == current_user.id, Category.user_id.is_(None))
    )
    if type:
        query = query.filter(Category.type == type)
        
    return query.order_by(Category.name).all()


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a specific custom category."""
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == current_user.id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found or is a system category")

    # If renaming, check duplicates
    if category_in.name and category_in.name.lower() != category.name.lower():
        existing = db.query(Category).filter(
            Category.name.ilike(category_in.name),
            or_(Category.user_id == current_user.id, Category.user_id.is_(None))
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category with this name already exists")

    update_data = category_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a custom category."""
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == current_user.id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found or is a system category")

    db.delete(category)
    db.commit()
    return None
