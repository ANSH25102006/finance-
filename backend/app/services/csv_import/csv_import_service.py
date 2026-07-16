from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.transaction import Transaction
from app.services.csv_import.csv_validator import CSVValidator
from app.services.csv_import.csv_parser import CSVParser
from app.services.csv_import.csv_mapper import CSVMapper
from app.services.csv_import.import_schema import CSVPreviewResponse, NormalizedTransactionPreview, CSVImportSummaryResponse


class CSVImportService:
    def preview_csv(self, filename: str, content_type: str, file_bytes: bytes, format_key: str) -> CSVPreviewResponse:
        """Run validation, parsing, and mapping pipelines sequentially to generate transaction previews."""
        # 1. Metadata validations
        CSVValidator.validate_file_metadata(filename, content_type, len(file_bytes))

        # 2. Parse file rows
        headers, parsed_rows = CSVParser.parse_csv_bytes(file_bytes, format_key)

        # 3. Check header column matches
        CSVValidator.validate_format_headers(headers, format_key)

        if not parsed_rows:
            raise HTTPException(status_code=400, detail="No transaction data rows found after statement headers.")

        # 4. Map records to normalized layout
        transactions = []
        for idx, row in enumerate(parsed_rows):
            try:
                tx_preview = CSVMapper.map_row_to_preview(row, format_key)
                transactions.append(tx_preview)
            except HTTPException as e:
                # Enriched context detail with row indices for easier client debugging
                raise HTTPException(
                    status_code=400,
                    detail=f"Error parsing row {idx + 1}: {e.detail}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unhandled error mapping row {idx + 1}: {str(e)}"
                )

        return CSVPreviewResponse(
            bank_format=format_key,
            total_parsed=len(transactions),
            transactions=transactions
        )

    def import_transactions(
        self,
        db: Session,
        user_id: UUID,
        account_id: UUID,
        filename: str,
        content_type: str,
        file_bytes: bytes,
        format_key: str
    ) -> CSVImportSummaryResponse:
        """Parse statement, isolate duplicate entries, and bulk insert new records inside a database transaction."""
        # 1. Parse and validate the statement (re-parsing to avoid relying on client-side state)
        preview = self.preview_csv(filename, content_type, file_bytes, format_key)
        
        if not preview.transactions:
            return CSVImportSummaryResponse(
                total_rows=0,
                imported=0,
                duplicates=0,
                failed=0,
                message="No transactions found in statement."
            )

        # 2. Extract boundary dates to query only target records
        dates = [tx.date for tx in preview.transactions]
        min_date = min(dates)
        max_date = max(dates)

        # 3. Query existing records for duplicate comparisons
        existing_records = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.account_id == account_id,
            Transaction.transaction_date >= min_date,
            Transaction.transaction_date <= max_date
        ).all()

        # Build in-memory lookup keys
        existing_lookup = {
            (tx.transaction_date, round(float(tx.amount), 2), (tx.description or "").strip())
            for tx in existing_records
        }

        # 4. Map and filter records
        transactions_to_insert = []
        duplicates_count = 0

        for tx in preview.transactions:
            key = (tx.date, round(tx.amount, 2), (tx.description or "").strip())
            if key in existing_lookup:
                duplicates_count += 1
                continue

            db_tx = Transaction(
                user_id=user_id,
                account_id=account_id,
                amount=tx.amount,
                transaction_type=tx.transaction_type,
                transaction_date=tx.date,
                description=tx.description,
                merchant=tx.merchant,
                notes=f"Reference: {tx.reference}" if tx.reference else None
            )
            transactions_to_insert.append(db_tx)

        # 5. Bulk insert with SQLAlchemy inside a single atomic transaction
        if transactions_to_insert:
            try:
                db.add_all(transactions_to_insert)
                db.commit()
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Database transaction failure. Rolling back all inserts. Error: {str(e)}"
                )

        return CSVImportSummaryResponse(
            total_rows=len(preview.transactions),
            imported=len(transactions_to_insert),
            duplicates=duplicates_count,
            failed=0,
            message="Import completed successfully."
        )
