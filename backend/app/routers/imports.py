from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.services.csv_import.csv_import_service import CSVImportService
from app.services.csv_import.import_schema import CSVPreviewResponse, CSVImportSummaryResponse

router = APIRouter(prefix="/import", tags=["CSV Import"])


@router.post("/csv-preview", response_model=CSVPreviewResponse)
async def csv_preview(
    bank_format: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
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
        format_key=bank_format
    )


@router.post("/import-transactions", response_model=CSVImportSummaryResponse)
async def import_transactions(
    bank_format: str = Form(...),
    account_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import transactions from statement into the database, skipping matching entries."""
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
