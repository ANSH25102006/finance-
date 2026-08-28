import re
from datetime import datetime
from typing import Dict
from fastapi import HTTPException

from app.services.csv_import.bank_formats import BANK_FORMATS
from app.services.csv_import.import_schema import NormalizedTransactionPreview


class CSVMapper:
    @staticmethod
    def map_row_to_preview(row: Dict[str, str], format_key: str) -> NormalizedTransactionPreview:
        """Parse raw CSV row dictionary into standard NormalizedTransactionPreview model."""
        cfg = BANK_FORMATS[format_key]

        # 1. Parse Date
        date_str = row.get(cfg["date_col"], "").strip()
        if not date_str:
            raise HTTPException(status_code=400, detail=f"Missing transaction date in row: {row}")

        parsed_date = None
        for fmt in cfg["date_formats"]:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue

        if parsed_date is None:
            raise HTTPException(
                status_code=400,
                detail=f"Could not parse transaction date '{date_str}' matching formats {cfg['date_formats']} in row: {row}"
            )

        # 2. Parse Description
        description = row.get(cfg["desc_col"], "").strip()
        if not description:
            raise HTTPException(status_code=400, detail=f"Missing description/narration in row: {row}")

        # 3. Clean and parse amount float values
        def clean_float(val_str: str) -> float:
            if not val_str:
                return 0.0
            # Remove any characters except digits, dots, and minus signs
            cleaned = re.sub(r"[^\d\.\-]", "", val_str)
            try:
                return float(cleaned) if cleaned else 0.0
            except ValueError:
                return 0.0

        amount = 0.0
        tx_type = "expense"

        if "withdrawal_col" in cfg and "deposit_col" in cfg:
            withdrawal_str = row.get(cfg["withdrawal_col"], "").strip()
            deposit_str = row.get(cfg["deposit_col"], "").strip()

            withdrawal_val = clean_float(withdrawal_str)
            deposit_val = clean_float(deposit_str)

            if withdrawal_val > 0.0:
                amount = withdrawal_val
                tx_type = "expense"
            elif deposit_val > 0.0:
                amount = deposit_val
                tx_type = "income"
            else:
                # If float is 0.0, check if the string had contents (e.g. zero-amount transaction or parse error)
                if withdrawal_str and not deposit_str:
                    amount = withdrawal_val
                    tx_type = "expense"
                elif deposit_str and not withdrawal_str:
                    amount = deposit_val
                    tx_type = "income"
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Row must contain either withdrawal or deposit amount: {row}"
                    )
        else:
            # Single Amount column (Generic Format)
            amt_str = row.get(cfg["amount_col"], "").strip()
            amt_val = clean_float(amt_str)

            type_col = cfg.get("type_col")
            if type_col and row.get(type_col):
                t_str = row.get(type_col, "").strip().upper()
                if t_str in ["DR", "DEBIT", "EXPENSE", "WITHDRAWAL", "W"]:
                    amount = abs(amt_val)
                    tx_type = "expense"
                elif t_str in ["CR", "CREDIT", "INCOME", "DEPOSIT", "D"]:
                    amount = abs(amt_val)
                    tx_type = "income"
                else:
                    if amt_val < 0.0:
                        amount = abs(amt_val)
                        tx_type = "expense"
                    else:
                        amount = amt_val
                        tx_type = "income"
            else:
                if amt_val < 0.0:
                    amount = abs(amt_val)
                    tx_type = "expense"
                else:
                    amount = amt_val
                    tx_type = "income"

        if amount <= 0.0:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transaction amount: {amount}. Amount must be positive in row: {row}"
            )

        # 4. Extract optional reference details
        ref_col = cfg.get("ref_col")
        reference = None
        if ref_col and row.get(ref_col):
            reference = row.get(ref_col, "").strip() or None

        # 5. Extract merchant name (heuristic)
        merchant = None
        upi_match = re.search(r"UPI/([^/]+)", description, re.IGNORECASE)
        if upi_match:
            merchant = upi_match.group(1).strip()
        else:
            # Fallback: grab first two words of narration
            words = description.split()
            if words:
                merchant = " ".join(words[:2]).strip()

        def sanitize_cell(text: str | None) -> str | None:
            if not text:
                return text
            # Strip dangerous formula prefixes to prevent CSV injection
            if text.startswith(('=', '+', '-', '@', '\t', '\r')):
                return text.lstrip('=+-@\t\r').strip()
            return text

        description = sanitize_cell(description) or description
        merchant = sanitize_cell(merchant)
        reference = sanitize_cell(reference)

        return NormalizedTransactionPreview(
            date=parsed_date,
            description=description,
            amount=amount,
            transaction_type=tx_type,
            merchant=merchant,
            reference=reference,
            raw_data=row
        )
