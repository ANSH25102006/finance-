import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import date, datetime, timezone, timedelta

from app.database import Base
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.models.goal import Goal
from app.services.audit_service import AuditService


class TestAuditEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create an in-memory SQLite database for unit testing
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        # Create a test user
        self.user_id = uuid.uuid4()
        self.user = User(
            id=self.user_id,
            email=f"test_{self.user_id}@example.com",
            password_hash="hashedpassword123"
        )
        self.db.add(self.user)
        self.db.commit()

        # Seed global categories
        self.food_cat = Category(id=uuid.uuid4(), name="Food & Dining", type="expense")
        self.shopping_cat = Category(id=uuid.uuid4(), name="Shopping", type="expense")
        self.salary_cat = Category(id=uuid.uuid4(), name="Salary", type="income")
        self.db.add_all([self.food_cat, self.shopping_cat, self.salary_cat])
        
        # Create a checking account
        self.account_id = uuid.uuid4()
        self.account = Account(
            id=self.account_id,
            user_id=self.user_id,
            name="Checking Account",
            balance=10000.0,
            currency="INR",
            icon="Bank",
            color="#3b82f6"
        )
        self.db.add(self.account)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_empty_database(self):
        """Verify audit engine does not crash when user has no transactions, budgets, or goals."""
        service = AuditService(self.db, self.user_id)
        result = service.run_financial_audit()

        self.assertEqual(result["summary"]["current_balance"], 10000.0)
        self.assertEqual(result["summary"]["total_income"], 0.0)
        self.assertEqual(result["summary"]["total_expenses"], 0.0)
        self.assertEqual(result["summary"]["net_cash_flow"], 0.0)
        self.assertEqual(result["summary"]["savings_rate"], 0.0)
        self.assertEqual(result["summary"]["expense_ratio"], 0.0)
        self.assertEqual(result["budgets"], [])
        self.assertEqual(result["goals"], [])
        self.assertEqual(result["categories"]["items"], [])
        self.assertEqual(result["merchants"]["items"], [])
        self.assertTrue(len(result["insights"]) >= 1)  # Zero income warning should trigger

    def test_only_expenses(self):
        """Verify aggregates when user only records expenses."""
        tx1 = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            account_id=self.account_id,
            category_id=self.food_cat.id,
            amount=500.0,
            transaction_type="expense",
            merchant="McDonalds",
            transaction_date=date.today(),
            description="Dinner out"
        )
        self.db.add(tx1)
        self.db.commit()

        service = AuditService(self.db, self.user_id)
        result = service.run_financial_audit()

        self.assertEqual(result["summary"]["total_income"], 0.0)
        self.assertEqual(result["summary"]["total_expenses"], 500.0)
        self.assertEqual(result["summary"]["net_cash_flow"], -500.0)
        self.assertEqual(result["summary"]["savings_rate"], 0.0)

    def test_only_income(self):
        """Verify metrics when user only logs income."""
        tx1 = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            account_id=self.account_id,
            category_id=self.salary_cat.id,
            amount=15000.0,
            transaction_type="income",
            merchant="TCS",
            transaction_date=date.today(),
            description="Salary credit"
        )
        self.db.add(tx1)
        self.db.commit()

        service = AuditService(self.db, self.user_id)
        result = service.run_financial_audit()

        self.assertEqual(result["summary"]["total_income"], 15000.0)
        self.assertEqual(result["summary"]["total_expenses"], 0.0)
        self.assertEqual(result["summary"]["net_cash_flow"], 15000.0)
        self.assertEqual(result["summary"]["savings_rate"], 100.0)
        self.assertEqual(result["summary"]["expense_ratio"], 0.0)

    def test_negative_cash_flow_and_overspent_budgets(self):
        """Verify risk detection for negative cashflow and overspent budget targets."""
        # Seed budget for current month/year
        today = date.today()
        b1 = Budget(
            id=uuid.uuid4(),
            user_id=self.user_id,
            category_id=self.shopping_cat.id,
            amount=100.0,
            month=today.month,
            year=today.year
        )
        self.db.add(b1)

        # Salary income = 1000
        tx1 = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            account_id=self.account_id,
            category_id=self.salary_cat.id,
            amount=1000.0,
            transaction_type="income",
            merchant="Upwork",
            transaction_date=today,
            description="Salary payment"
        )
        # Shopping expense = 1200 (over budget and negative cash flow)
        tx2 = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            account_id=self.account_id,
            category_id=self.shopping_cat.id,
            amount=1200.0,
            transaction_type="expense",
            merchant="Zara",
            transaction_date=today,
            description="Clothes buying"
        )
        self.db.add_all([tx1, tx2])
        self.db.commit()

        service = AuditService(self.db, self.user_id)
        result = service.run_financial_audit()

        # Check budgets status
        self.assertEqual(result["budgets"][0]["status"], "Exceeded")

        # Check risk indicators
        risk_types = [r["type"] for r in result["risks"]]
        self.assertIn("Negative Cash Flow", risk_types)
        self.assertIn("Overspent Budgets", risk_types)

    def test_goals_completed(self):
        """Verify goal progress calculation and completion status."""
        g1 = Goal(
            id=uuid.uuid4(),
            user_id=self.user_id,
            name="Emergency Fund",
            target_amount=5000.0,
            current_amount=5500.0,
            monthly_contribution=100.0
        )
        self.db.add(g1)
        self.db.commit()

        service = AuditService(self.db, self.user_id)
        result = service.run_financial_audit()

        self.assertEqual(result["goals"][0]["completion_pct"], 110.0)
        self.assertEqual(result["goals"][0]["estimated_completion"], "Completed")
        self.assertEqual(result["goals"][0]["status"], "Completed")


if __name__ == "__main__":
    unittest.main()
