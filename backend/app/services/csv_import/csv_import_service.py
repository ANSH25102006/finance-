import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.transaction import Transaction
from app.services.csv_import.csv_validator import CSVValidator
from app.services.csv_import.csv_parser import CSVParser
from app.services.csv_import.csv_mapper import CSVMapper
from app.services.csv_import.import_schema import CSVPreviewResponse, NormalizedTransactionPreview, CSVImportSummaryResponse

logger = logging.getLogger(__name__)

class CSVImportService:
    def preview_csv(self, filename: str, content_type: str, file_bytes: bytes, format_key: str, db: Session = None, user_id: UUID = None) -> CSVPreviewResponse:
        """Run validation, parsing, and mapping pipelines sequentially to generate transaction previews."""
        # 1. Metadata validations
        CSVValidator.validate_file_metadata(filename, content_type, len(file_bytes))

        # Handle PDF and CSV parsing
        if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
            from app.services.csv_import.pdf_parser import parse_pdf_to_csv_string
            logger.info(f"Converting PDF {filename} to CSV for processing...")
            csv_data = parse_pdf_to_csv_string(file_bytes, format_key)
            actual_bytes = csv_data.encode('utf-8')
        else:
            actual_bytes = file_bytes

        # 2. Parse file rows
        headers, parsed_rows = CSVParser.parse_csv_bytes(actual_bytes, format_key)

        # 3. Check header column matches
        CSVValidator.validate_format_headers(headers, format_key)

        if not parsed_rows:
            raise HTTPException(status_code=400, detail="No transaction data rows found after statement headers.")

        # 4. Map records to normalized layout
        from app.services.merchant.merchant_service import MerchantService
        merchant_service = MerchantService()

        transactions = []
        for idx, row in enumerate(parsed_rows):
            try:
                tx_preview = CSVMapper.map_row_to_preview(row, format_key)
                
                # Recognize merchant details using Merchant Intelligence
                recognition = merchant_service.recognize(tx_preview.description, db, user_id)
                tx_preview.merchant = recognition["merchant"]
                tx_preview.category = recognition["category"]
                tx_preview.confidence = recognition["confidence"]

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
        preview = self.preview_csv(filename, content_type, file_bytes, format_key, db=db, user_id=user_id)
        
        if not preview.transactions:
            return CSVImportSummaryResponse(
                total_rows=0,
                imported=0,
                duplicates=0,
                failed=0,
                message="No transactions found in statement.",
                transactions=[]
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
        from app.models.category import Category
        from sqlalchemy import or_

        category_aesthetics = {
            "Food Delivery": {"icon": "Utensils", "color": "#ef4444"},
            "Shopping": {"icon": "ShoppingBag", "color": "#ec4899"},
            "Transport": {"icon": "Car", "color": "#3b82f6"},
            "Entertainment": {"icon": "Play", "color": "#8b5cf6"},
            "Healthcare": {"icon": "Activity", "color": "#10b981"},
            "Utilities": {"icon": "Zap", "color": "#f59e0b"},
            "Telecom": {"icon": "Phone", "color": "#06b6d4"},
            "Payments": {"icon": "CreditCard", "color": "#64748b"},
            "Salary": {"icon": "DollarSign", "color": "#22c55e"},
            "Transfer": {"icon": "ArrowRightLeft", "color": "#6366f1"},
            "Unknown": {"icon": "HelpCircle", "color": "#94a3b8"}
        }

        local_category_cache = {}
        transactions_to_insert = []
        duplicates_count = 0

        for tx in preview.transactions:
            key = (tx.date, round(tx.amount, 2), (tx.description or "").strip())
            if key in existing_lookup:
                duplicates_count += 1
                continue

            # Look up or create category
            cat_name = tx.category or "Unknown"
            if cat_name in local_category_cache:
                db_cat = local_category_cache[cat_name]
            else:
                db_cat = db.query(Category).filter(
                    Category.name.ilike(cat_name),
                    or_(Category.user_id == user_id, Category.user_id.is_(None))
                ).first()
                
                if not db_cat:
                    # Create new category dynamic record
                    aest = category_aesthetics.get(cat_name, {"icon": "HelpCircle", "color": "#94a3b8"})
                    db_cat = Category(
                        user_id=user_id,
                        name=cat_name,
                        type=tx.transaction_type,
                        icon=aest["icon"],
                        color=aest["color"]
                    )
                    db.add(db_cat)
                    db.flush()  # Generate UUID ID for category assignment
                local_category_cache[cat_name] = db_cat

            db_tx = Transaction(
                user_id=user_id,
                account_id=account_id,
                amount=tx.amount,
                transaction_type=tx.transaction_type,
                transaction_date=tx.date,
                description=tx.description,
                merchant=tx.merchant,
                confidence_score=tx.confidence,
                category_id=db_cat.id,
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
            message="Import completed successfully.",
            transactions=preview.transactions
        )
