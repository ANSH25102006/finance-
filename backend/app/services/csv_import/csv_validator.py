from fastapi import HTTPException
from typing import List
from app.services.csv_import.bank_formats import BANK_FORMATS


class CSVValidator:
    @staticmethod
    def validate_file_metadata(filename: str, content_type: str, file_size: int):
        """Validate basic file attributes (type and size constraints)."""
        # Validate size (Max 5MB)
        if file_size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 5MB.")

        # Validate extension
        ext = filename.lower()
        if not (ext.endswith(".csv") or ext.endswith(".pdf")):
            raise HTTPException(status_code=400, detail="Invalid file type. Only CSV (.csv) or PDF (.pdf) files are supported.")

        # Validate MIME type
        valid_mime_types = {
            "text/csv",
            "application/vnd.ms-excel",
            "text/plain",
            "text/x-csv",
            "application/csv",
            "application/x-csv",
            "text/comma-separated-values",
            "application/pdf",
            "application/x-pdf",
            "application/acrobat",
            "applications/vnd.pdf",
            "text/pdf",
            "text/x-pdf"
        }
        if content_type and content_type.lower() not in valid_mime_types and not (ext.endswith(".csv") or ext.endswith(".pdf")):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file content-type '{content_type}'. Only CSV or PDF files are supported."
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="The uploaded statement file is empty.")

    @staticmethod
    def validate_format_headers(headers: List[str], format_key: str):
        """Ensure all required header columns for the chosen format are present in the CSV."""
        if format_key not in BANK_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: '{format_key}'. Supported: {list(BANK_FORMATS.keys())}"
            )

        cfg = BANK_FORMATS[format_key]
        required = cfg["required_headers"]

        # Normalize header strings to prevent whitespace discrepancies
        cleaned_headers = [h.strip().replace('"', '').replace("'", "") for h in headers if h]

        missing = [req for req in required if req not in cleaned_headers]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns for format '{format_key}': {missing}. Headers found: {cleaned_headers}"
            )
