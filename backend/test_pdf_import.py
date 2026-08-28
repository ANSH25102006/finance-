import pytest
from app.services.csv_import.csv_validator import CSVValidator
from app.services.csv_import.csv_mapper import CSVMapper
from fastapi import HTTPException

def test_pdf_metadata_validation():
    # PDF metadata should pass validation
    CSVValidator.validate_file_metadata("statement.pdf", "application/pdf", 1024)
    CSVValidator.validate_file_metadata("statement.PDF", "application/x-pdf", 2048)

    # Invalid extension should fail
    with pytest.raises(HTTPException) as exc:
        CSVValidator.validate_file_metadata("statement.txt", "text/plain", 1024)
    assert exc.value.status_code == 400

def test_csv_formula_sanitization():
    row = {
        "Date": "20/08/2026",
        "Narration": "=SUM(A1:A10)",
        "Withdrawal Amt.": "500.00",
        "Deposit Amt.": ""
    }
    tx = CSVMapper.map_row_to_preview(row, "hdfc")
    # Formula prefix should be stripped
    assert not tx.description.startswith("=")
    assert tx.amount == 500.0
