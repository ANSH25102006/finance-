import unittest
import uuid
import csv
import io
from datetime import date
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.services.csv_import.csv_import_service import CSVImportService
from app.main import app

# In-memory SQLite for testing
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
SessionTesting = sessionmaker(bind=engine)


class TestImportWorkflowService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(engine)

    def setUp(self):
        self.db = SessionTesting()
        
        # Create a test user
        self.user_id = uuid.uuid4()
        self.user = User(
            id=self.user_id,
            email=f"test_{self.user_id}@example.com",
            password_hash="hashedpassword123"
        )
        self.db.add(self.user)
        
        # Create a checking account
        self.account_id = uuid.uuid4()
        self.account = Account(
            id=self.account_id,
            user_id=self.user_id,
            name="Checking Account",
            balance=5000.0,
            currency="INR",
            icon="Bank",
            color="#3b82f6"
        )
        self.db.add(self.account)
        self.db.commit()
        
        self.service = CSVImportService()

    def tearDown(self):
        self.db.close()
        # Drop all rows after each test to ensure test isolation
        db = SessionTesting()
        db.query(Transaction).delete()
        db.query(Account).delete()
        db.query(User).delete()
        db.commit()
        db.close()

    def test_successful_import(self):
        """Verify standard HDFC statement inserts transactions correctly."""
        csv_data = (
            "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
            "10/01/26,Starbucks Coffee,REF123,10/01/26,350.00,,10000.00\n"
            "12/01/26,Upwork Payout,REF456,12/01/26,,5000.00,15000.00\n"
        )
        
        res = self.service.import_transactions(
            db=self.db,
            user_id=self.user_id,
            account_id=self.account_id,
            filename="hdfc.csv",
            content_type="text/csv",
            file_bytes=csv_data.encode("utf-8"),
            format_key="hdfc"
        )
        
        self.assertEqual(res.total_rows, 2)
        self.assertEqual(res.imported, 2)
        self.assertEqual(res.duplicates, 0)
        
        # Query DB to assert records
        txs = self.db.query(Transaction).filter(Transaction.user_id == self.user_id).all()
        self.assertEqual(len(txs), 2)

    def test_duplicate_and_partial_duplicate_import(self):
        """Verify identical rows are ignored, while new rows are imported in a subsequent run."""
        csv_data_1 = (
            "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
            "10/01/26,Starbucks Coffee,REF123,10/01/26,350.00,,10000.00\n"
        )
        
        # First import
        res1 = self.service.import_transactions(
            db=self.db,
            user_id=self.user_id,
            account_id=self.account_id,
            filename="hdfc.csv",
            content_type="text/csv",
            file_bytes=csv_data_1.encode("utf-8"),
            format_key="hdfc"
        )
        self.assertEqual(res1.imported, 1)

        # Second import: includes the first transaction + a new one
        csv_data_2 = (
            "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
            "10/01/26,Starbucks Coffee,REF123,10/01/26,350.00,,10000.00\n"
            "15/01/26,Netflix Subscription,REF999,15/01/26,699.00,,9301.00\n"
        )
        res2 = self.service.import_transactions(
            db=self.db,
            user_id=self.user_id,
            account_id=self.account_id,
            filename="hdfc.csv",
            content_type="text/csv",
            file_bytes=csv_data_2.encode("utf-8"),
            format_key="hdfc"
        )
        
        self.assertEqual(res2.total_rows, 2)
        self.assertEqual(res2.imported, 1)
        self.assertEqual(res2.duplicates, 1)
        
        # Verify db total rows
        txs = self.db.query(Transaction).all()
        self.assertEqual(len(txs), 2)

    def test_database_rollback_on_integrity_error(self):
        """Verify that any database error rolls back the entire batch transaction."""
        csv_data = (
            "Transaction Date,Value Date,Cheque No.,Description,Withdrawal (Dr),Deposit (Cr),Balance\n"
            "15/01/2026,15/01/2026,CHQ777,Amazon In,1200.00,0.00,8800.00\n"
        )
        
        # We temporarily mock db.commit to raise an exception, triggering rollback
        from unittest.mock import MagicMock
        original_commit = self.db.commit
        self.db.commit = MagicMock(side_effect=Exception("Simulated integrity error"))
        
        try:
            with self.assertRaises(HTTPException) as ctx:
                self.service.import_transactions(
                    db=self.db,
                    user_id=self.user_id,
                    account_id=self.account_id,
                    filename="icici.csv",
                    content_type="text/csv",
                    file_bytes=csv_data.encode("utf-8"),
                    format_key="icici"
                )
            self.assertEqual(ctx.exception.status_code, 500)
            self.assertIn("Database transaction failure", ctx.exception.detail)
            
            # Restore commit to query database
            self.db.commit = original_commit
            
            # Verify no rows were added to the DB because of rollback
            count = self.db.query(Transaction).count()
            self.assertEqual(count, 0)
        finally:
            self.db.commit = original_commit

    def test_large_import_performance(self):
        """Verify bulk saving performance for large statement uploads (1,000 rows)."""
        # Build 1000 rows stream
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Description", "Amount", "Type"])
        for i in range(1000):
            writer.writerow([f"2026-01-01", f"Transaction {i}", "100.00", "DR"])
            
        csv_data = output.getvalue()
        
        res = self.service.import_transactions(
            db=self.db,
            user_id=self.user_id,
            account_id=self.account_id,
            filename="generic.csv",
            content_type="text/csv",
            file_bytes=csv_data.encode("utf-8"),
            format_key="generic"
        )
        self.assertEqual(res.imported, 1000)
        self.assertEqual(self.db.query(Transaction).count(), 1000)


class TestImportWorkflowAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_unauthorized_request(self):
        """Verify that requests without JWT validation headers are rejected with 401."""
        response = self.client.post(
            "/api/import/import-transactions",
            data={"bank_format": "hdfc", "account_id": str(uuid.uuid4())},
            files={"file": ("test.csv", b"Date,Amount\n", "text/csv")}
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
