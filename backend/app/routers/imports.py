from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.services.csv_import.csv_import_service import CSVImportService
from app.services.csv_import.import_schema import CSVPreviewResponse, CSVImportSummaryResponse
from app.dependencies.rate_limit import RateLimiter

router = APIRouter(prefix="/import", tags=["CSV Import"])

preview_limiter = RateLimiter(10, 60)
import_limiter = RateLimiter(10, 60)


@router.post("/csv-preview", response_model=CSVPreviewResponse, dependencies=[Depends(preview_limiter)])
async def csv_preview(
    bank_format: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Parse an uploaded bank statement CSV file and return a normalized transaction preview."""
    # Read the file contents as bytes
    file_bytes = await file.read()

    # Delegate parsing to CSVImportService
    service = CSVImportService()
    return service.preview_csv(
        filename=file.filename or "statement.csv",
        content_type=file.content_type or "text/csv",
        file_bytes=file_bytes,
        format_key=bank_format,
        db=db,
        user_id=current_user.id
    )


@router.post("/import-transactions", response_model=CSVImportSummaryResponse, dependencies=[Depends(import_limiter)])
async def import_transactions(
    bank_format: str = Form(...),
    account_id: UUID = Form(...),
    file: UploadFile = File(...),
    merchant_overrides: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import transactions from statement into the database, skipping matching entries."""
    # Verify account ownership to prevent IDOR vulnerabilities
    from app.models.account import Account
    from fastapi import HTTPException, status

    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.user_id == current_user.id)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or access denied."
        )

    # Process merchant overrides
    if merchant_overrides:
        import json
        from app.services.merchant.merchant_service import MerchantService
        try:
            overrides = json.loads(merchant_overrides)
            ms = MerchantService()
            for ov in overrides:
                ms.learn_merchant(
                    db=db,
                    user_id=current_user.id,
                    raw_name=ov.get("raw_name"),
                    normalized_name=ov.get("normalized_name"),
                    category_id=ov.get("category_id")
                )
        except Exception as e:
            # We log but continue, so bad overrides don't break the import completely
            import logging
            logging.getLogger(__name__).warning(f"Failed to process merchant overrides: {e}")

    file_bytes = await file.read()
    service = CSVImportService()
    return service.import_transactions(
        db=db,
        user_id=current_user.id,
        account_id=account_id,
        filename=file.filename or "statement.csv",
        content_type=file.content_type or "text/csv",
        file_bytes=file_bytes,
        format_key=bank_format
    )
