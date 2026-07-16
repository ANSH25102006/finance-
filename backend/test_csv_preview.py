import unittest
from fastapi import HTTPException
from app.services.csv_import.csv_import_service import CSVImportService


class TestCSVImportPreview(unittest.TestCase):
    def setUp(self):
        self.service = CSVImportService()

    def test_valid_hdfc_preview(self):
        """Verify successful mapping of HDFC statement layout with header offset."""
        csv_data = (
            "HDFC Bank Statement\n"
            "Period: Jan 2026\n"
            "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
            "10/01/26,Starbucks Coffee,REF123,10/01/26,350.00,,10000.00\n"
            "12/01/26,Upwork Payout,REF456,12/01/26,,5000.00,15000.00\n"
        )
        res = self.service.preview_csv(
            filename="hdfc.csv",
            content_type="text/csv",
            file_bytes=csv_data.encode("utf-8"),
            format_key="hdfc"
        )
        self.assertEqual(res.bank_format, "hdfc")
        self.assertEqual(res.total_parsed, 2)
        
        # MCDonalds transaction check (Withdrawal -> expense)
        tx1 = res.transactions[0]
        self.assertEqual(tx1.amount, 350.0)
        self.assertEqual(tx1.transaction_type, "expense")
        self.assertEqual(tx1.merchant, "Starbucks Coffee")
        self.assertEqual(tx1.reference, "REF123")

        # Income check
        tx2 = res.transactions[1]
        self.assertEqual(tx2.amount, 5000.0)
        self.assertEqual(tx2.transaction_type, "income")
        self.assertEqual(tx2.merchant, "Upwork Payout")

    def test_valid_icici_preview(self):
        """Verify successful mapping of ICICI statement layout."""
        csv_data = (
            "Transaction Date,Value Date,Cheque No.,Description,Withdrawal (Dr),Deposit (Cr),Balance\n"
            "15/01/2026,15/01/2026,CHQ777,Amazon In,1200.00,0.00,8800.00\n"
        )
        res = self.service.preview_csv(
            filename="icici.csv",
            content_type="text/csv",
            file_bytes=csv_data.encode("utf-8"),
            format_key="icici"
        )
        self.assertEqual(res.bank_format, "icici")
        self.assertEqual(res.total_parsed, 1)
        tx = res.transactions[0]
        self.assertEqual(tx.amount, 1200.0)
        self.assertEqual(tx.transaction_type, "expense")
        self.assertEqual(tx.merchant, "Amazon In")

    def test_valid_generic_preview(self):
        """Verify generic standard layout mappings."""
        csv_data = (
            "Date,Description,Amount,Type,Reference\n"
            "2026-01-20,Zomato Food Order,150.00,DR,REF09\n"
            "2026-01-22,Salary Credited,25000.00,CR,REF10\n"
        )
        res = self.service.preview_csv(
            filename="generic.csv",
            content_type="text/csv",
            file_bytes=csv_data.encode("utf-8"),
            format_key="generic"
        )
        self.assertEqual(res.bank_format, "generic")
        self.assertEqual(res.total_parsed, 2)
        self.assertEqual(res.transactions[0].transaction_type, "expense")
        self.assertEqual(res.transactions[1].transaction_type, "income")

    def test_unsupported_format(self):
        """Verify exception on choosing non-supported bank structures."""
        csv_data = "Date,Narration,Amount\n2026-01-01,Test,100"
        with self.assertRaises(HTTPException) as ctx:
            self.service.preview_csv(
                filename="statement.csv",
                content_type="text/csv",
                file_bytes=csv_data.encode("utf-8"),
                format_key="chase"
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Unsupported format", ctx.exception.detail)

    def test_empty_file(self):
        """Verify empty files metadata validations."""
        with self.assertRaises(HTTPException) as ctx:
            self.service.preview_csv(
                filename="empty.csv",
                content_type="text/csv",
                file_bytes=b"",
                format_key="hdfc"
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("empty", ctx.exception.detail)

    def test_missing_headers(self):
        """Verify header mapping column absence validation checks."""
        # Narration is missing
        csv_data = "Date,Withdrawal Amt.,Deposit Amt.\n10/01/26,100,,"
        with self.assertRaises(HTTPException) as ctx:
            self.service.preview_csv(
                filename="hdfc.csv",
                content_type="text/csv",
                file_bytes=csv_data.encode("utf-8"),
                format_key="hdfc"
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Could not locate statement headers", ctx.exception.detail)

    def test_malformed_csv_rows(self):
        """Verify parsing errors on row content errors (e.g. invalid date)."""
        csv_data = (
            "Date,Narration,Withdrawal Amt.,Deposit Amt.\n"
            "invalid_date,Starbucks Coffee,350.00,,\n"
        )
        with self.assertRaises(HTTPException) as ctx:
            self.service.preview_csv(
                filename="hdfc.csv",
                content_type="text/csv",
                file_bytes=csv_data.encode("utf-8"),
                format_key="hdfc"
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Could not parse transaction date", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
