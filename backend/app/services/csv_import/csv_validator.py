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
        if not filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Invalid file type. Only CSV files (.csv) are supported.")

        if file_size == 0:
            raise HTTPException(status_code=400, detail="The uploaded CSV file is empty.")

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
