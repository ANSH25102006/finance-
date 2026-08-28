# ============================================================
#  pdf_parser.py — Modular PDF bank statement parsing
# ============================================================

import io
import csv
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class PDFParserError(Exception):
    pass

def parse_pdf_to_csv_string(file_bytes: bytes, format_key: str) -> str:
    """
    Parses a bank PDF and converts its tabular data into a CSV string.
    This allows us to reuse the exact same CSV mapping logic.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber is not installed.")
        raise PDFParserError("PDF parsing requires pdfplumber to be installed on the server.")

    csv_output = io.StringIO()
    writer = csv.writer(csv_output)
    
    # Very simplistic PDF table extraction.
    # In a real-world scenario, you'd have specific bounding boxes for specific banks.
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        # We assume the first page contains headers if it's a statement, or we just extract all tables
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Clean up newlines inside cells
                    clean_row = [str(cell).replace('\n', ' ').strip() if cell else '' for cell in row]
                    writer.writerow(clean_row)
                    
    csv_string = csv_output.getvalue()
    if not csv_string.strip():
        raise PDFParserError("Could not extract any tabular data from this PDF.")
        
    return csv_string
