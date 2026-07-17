from pydantic import BaseModel, Field
from datetime import date
from typing import List, Dict, Optional


class NormalizedTransactionPreview(BaseModel):
    date: date
    description: str
    amount: float
    transaction_type: str  # 'income' or 'expense'
    merchant: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[int] = None
    reference: Optional[str] = None
    raw_data: Dict[str, str]


class CSVPreviewResponse(BaseModel):
    bank_format: str
    total_parsed: int
    transactions: List[NormalizedTransactionPreview]


class CSVImportSummaryResponse(BaseModel):
    total_rows: int
    imported: int
    duplicates: int
    failed: int
    message: str
    transactions: List[NormalizedTransactionPreview] = []
