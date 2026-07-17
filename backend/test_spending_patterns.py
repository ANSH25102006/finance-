import unittest
import uuid
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.services.ai.spending_pattern_service import SpendingPatternService


class TestSpendingPatterns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(cls.engine)
        cls.SessionTesting = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionTesting()
        self.user_id = uuid.uuid4()
        self.user = User(id=self.user_id, email=f"test_{self.user_id}@example.com", password_hash="hashed")
        self.db.add(self.user)
        self.db.commit()

        self.account_id = uuid.uuid4()
        self.account = Account(
            id=self.account_id,
            user_id=self.user_id,
            name="Test Account",
            balance=50000.0,
            currency="INR"
        )
        self.db.add(self.account)
        self.db.commit()

        # Categories
        self.food_cat = self.create_category("Food", "expense")
        self.shopping_cat = self.create_category("Shopping", "expense")
        self.service = SpendingPatternService()

    def tearDown(self):
        self.db.close()
        db = self.SessionTesting()
        db.query(Transaction).delete()
        db.query(Category).delete()
        db.query(Account).delete()
        db.query(User).delete()
        db.commit()
        db.close()

    def create_category(self, name: str, type_str: str) -> Category:
        cat = Category(id=uuid.uuid4(), user_id=self.user_id, name=name, type=type_str)
        self.db.add(cat)
        self.db.commit()
        return cat

    def add_tx(self, amount, merchant, tx_date, category, desc="Test"):
        tx = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            account_id=self.account_id,
            category_id=category.id,
            amount=amount,
            transaction_type="expense",
            merchant=merchant,
            transaction_date=tx_date,
            description=desc
        )
        self.db.add(tx)
        self.db.commit()
        return tx

    def test_basic_spending_analysis(self):
        # Weekdays vs Weekends in July 2026
        # July 1, 2026 (Wednesday) - weekday
        # July 4, 2026 (Saturday) - weekend
        self.add_tx(100.0, "Amazon", date(2026, 7, 1), self.shopping_cat)
        self.add_tx(500.0, "Swiggy", date(2026, 7, 4), self.food_cat)

        txs = self.db.query(Transaction).filter(Transaction.user_id == self.user_id).all()
        cats = self.db.query(Category).filter(Category.user_id == self.user_id).all()

        analysis = self.service.analyze_patterns(txs, cats)

        self.assertEqual(analysis["largest_category"], "Food")
        self.assertEqual(analysis["largest_cat_amount"], 500.0)
        self.assertEqual(analysis["avg_weekday_daily_spend"], 100.0)
        self.assertEqual(analysis["avg_weekend_daily_spend"], 500.0)

    def test_spending_spikes_detection(self):
        # Create runs to establish a median purchase size
        # Median of [50, 60, 70, 80, 100] is 70. 3x median is 210.
        self.add_tx(50.0, "M1", date(2026, 7, 1), self.shopping_cat)
        self.add_tx(60.0, "M2", date(2026, 7, 2), self.shopping_cat)
        self.add_tx(70.0, "M3", date(2026, 7, 3), self.shopping_cat)
        self.add_tx(80.0, "M4", date(2026, 7, 4), self.shopping_cat)
        self.add_tx(100.0, "M5", date(2026, 7, 5), self.shopping_cat)
        # Spike transaction: 500.0 (> 3x median)
        self.add_tx(500.0, "Spike Merchant", date(2026, 7, 6), self.shopping_cat)

        txs = self.db.query(Transaction).filter(Transaction.user_id == self.user_id).all()
        cats = self.db.query(Category).filter(Category.user_id == self.user_id).all()

        analysis = self.service.analyze_patterns(txs, cats)
        self.assertEqual(len(analysis["spikes"]), 1)
        self.assertEqual(analysis["spikes"][0]["merchant"], "Spike Merchant")
        self.assertEqual(analysis["spikes"][0]["amount"], 500.0)


if __name__ == "__main__":
    unittest.main()
