import csv
import io
from typing import List, Dict, Tuple
from fastapi import HTTPException
from app.services.csv_import.bank_formats import BANK_FORMATS


class CSVParser:
    @staticmethod
    def parse_csv_bytes(file_bytes: bytes, format_key: str) -> Tuple[List[str], List[Dict[str, str]]]:
        if format_key not in BANK_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: '{format_key}'. Supported: {list(BANK_FORMATS.keys())}"
            )

        decoded = None
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                decoded = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if decoded is None:
            raise HTTPException(
                status_code=400,
                detail="Failed to decode CSV encoding. Please upload UTF-8 or Latin-1 files."
            )

        # Split lines, preserving format
        lines = [line.strip() for line in decoded.splitlines() if line.strip()]
        if not lines:
            raise HTTPException(status_code=400, detail="CSV file is empty.")

        # Find header index matching Bank Format required fields
        cfg = BANK_FORMATS[format_key]
        required = cfg["required_headers"]

        header_index = -1
        headers = []

        for i, line in enumerate(lines):
            # Parse line with CSV reader to handle quoted fields correctly
            reader = csv.reader([line])
            try:
                row = next(reader)
            except (StopIteration, csv.Error):
                continue

            cleaned_row = [cell.strip().replace('"', '').replace("'", "") for cell in row if cell is not None]

            # Check if required headers are subset of this row
            if all(req in cleaned_row for req in required):
                header_index = i
                headers = cleaned_row
                break

        if header_index == -1:
            raise HTTPException(
                status_code=400,
                detail=f"Could not locate statement headers. Required headers for '{format_key}': {required}"
            )

        # Parse from the header line downwards
        data_content = "\n".join(lines[header_index:])
        reader = csv.DictReader(io.StringIO(data_content))

        parsed_rows = []
        for row in reader:
            cleaned_row = {}
            for k, v in row.items():
                if k is not None:
                    # Clean trailing characters or carriage returns
                    key = k.strip().replace('"', '').replace("'", "")
                    val = v.strip() if v is not None else ""

                    # Prevent CSV Formula Injection (=, +, -, @) on text fields
                    # Avoid prepending to negative numbers or decimal values
                    if val.startswith(('=', '+', '-', '@')) and not _is_number(val):
                        val = "'" + val

                    cleaned_row[key] = val

            # Skip empty lines or divider bars
            if any(cleaned_row.values()) and not all(val.startswith("---") for val in cleaned_row.values()):
                parsed_rows.append(cleaned_row)

        return headers, parsed_rows


def _is_number(val: str) -> bool:
    """Helper to detect if a text cell represents a decimal number."""
    try:
        cleaned = val.replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip()
        float(cleaned)
        return True
    except ValueError:
        return False
