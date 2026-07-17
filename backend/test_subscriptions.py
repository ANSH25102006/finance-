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
from app.services.ai.subscription_service import SubscriptionService


class TestSubscriptionService(unittest.TestCase):
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

        self.sub_cat = Category(id=uuid.uuid4(), user_id=self.user_id, name="Subscriptions", type="expense")
        self.db.add(self.sub_cat)
        self.db.commit()

        self.service = SubscriptionService()

    def tearDown(self):
        self.db.close()
        db = self.SessionTesting()
        db.query(Transaction).delete()
        db.query(Category).delete()
        db.query(Account).delete()
        db.query(User).delete()
        db.commit()
        db.close()

    def add_tx(self, amount, merchant, tx_date, desc="Test"):
        tx = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            account_id=self.account_id,
            category_id=self.sub_cat.id,
            amount=amount,
            transaction_type="expense",
            merchant=merchant,
            transaction_date=tx_date,
            description=desc
        )
        self.db.add(tx)
        self.db.commit()
        return tx

    def test_recurring_netflix_subscription(self):
        # Netflix billing spaced exactly 30 days apart
        self.add_tx(199.0, "Netflix", date(2026, 4, 1))
        self.add_tx(199.0, "Netflix", date(2026, 5, 1))
        self.add_tx(199.0, "Netflix", date(2026, 5, 31))

        txs = self.db.query(Transaction).filter(Transaction.user_id == self.user_id).all()
        result = self.service.detect_subscriptions(txs)

        self.assertEqual(len(result["active_subscriptions"]), 1)
        sub = result["active_subscriptions"][0]
        self.assertEqual(sub["merchant"], "Netflix")
        self.assertEqual(sub["monthly_amount"], 199.0)
        self.assertTrue(sub["matched_catalog"])
        self.assertEqual(sub["payment_consistency"], 100.0)

    def test_duplicate_netflix_subscriptions(self):
        # Two parallel cycles of Netflix
        # Run 1
        self.add_tx(199.0, "Netflix", date(2026, 4, 1))
        self.add_tx(199.0, "Netflix", date(2026, 5, 1))
        self.add_tx(199.0, "Netflix", date(2026, 5, 31))

        # Run 2 (different card or plan cycle)
        self.add_tx(199.0, "Netflix", date(2026, 4, 15))
        self.add_tx(199.0, "Netflix", date(2026, 5, 15))
        self.add_tx(199.0, "Netflix", date(2026, 6, 14))

        txs = self.db.query(Transaction).filter(Transaction.user_id == self.user_id).all()
        result = self.service.detect_subscriptions(txs)

        self.assertEqual(len(result["active_subscriptions"]), 2)
        self.assertEqual(len(result["duplicate_subscriptions"]), 1)
        self.assertEqual(result["duplicate_subscriptions"][0]["merchant"], "Netflix")
        self.assertEqual(result["duplicate_subscriptions"][0]["potential_savings_monthly"], 199.0)


if __name__ == "__main__":
    unittest.main()
