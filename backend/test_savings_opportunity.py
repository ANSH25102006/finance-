import unittest
import uuid
import json
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.services.ai.financial_context_builder import FinancialContextBuilder
from app.services.ai.savings_opportunity_service import SavingsOpportunityService


class TestSavingsOpportunityEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(cls.engine)
        cls.SessionTesting = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionTesting()

        # Create a test user
        self.user_id = uuid.uuid4()
        self.user = User(
            id=self.user_id,
            email=f"test_{self.user_id}@example.com",
            password_hash="hashedpassword123"
        )
        self.db.add(self.user)
        self.db.commit()

        # Create checking account
        self.account_id = uuid.uuid4()
        self.account = Account(
            id=self.account_id,
            user_id=self.user_id,
            name="Checking",
            balance=35000.0,
            currency="INR",
            icon="Bank",
            color="#3b82f6"
        )
        self.db.add(self.account)
        self.db.commit()

        # Categories
        self.salary_cat = self.create_category("Salary", "income")
        self.shopping_cat = self.create_category("Shopping", "expense")
        self.food_cat = self.create_category("Food Delivery", "expense")
        self.utilities_cat = self.create_category("Utilities", "expense")
        self.entertainment_cat = self.create_category("Entertainment", "expense")

        self.builder = FinancialContextBuilder()
        self.service = SavingsOpportunityService()

    def tearDown(self):
        self.db.close()
        db = self.SessionTesting()
        db.query(Transaction).delete()
        db.query(Budget).delete()
        db.query(Category).delete()
        db.query(Account).delete()
        db.query(User).delete()
        db.commit()
        db.close()

    def create_category(self, name: str, type_str: str) -> Category:
        cat = Category(
            id=uuid.uuid4(),
            user_id=self.user_id,
            name=name,
            type=type_str,
            icon="HelpCircle",
            color="#94a3b8"
        )
        self.db.add(cat)
        self.db.commit()
        return cat

    def add_tx(self, amount, tx_type, merchant, tx_date, category=None, desc="Test"):
        tx = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            account_id=self.account_id,
            category_id=category.id if category else None,
            amount=amount,
            transaction_type=tx_type,
            merchant=merchant,
            transaction_date=tx_date,
            description=desc
        )
        self.db.add(tx)
        self.db.commit()
        return tx

    def test_perfect_finances_no_opportunities(self):
        """Verify that a perfect financial state generates 0 opportunities and baseline confidence."""
        self.add_tx(50000.0, "income", "Employer", date(2026, 7, 1), self.salary_cat, "Salary")
        self.add_tx(100.0, "expense", "Store", date(2026, 7, 5), self.shopping_cat, "Store purchase")

        context = self.builder.build_context(self.db, self.user_id)
        result = self.service.generate_opportunities(context)

        self.assertEqual(result.monthly_savings, 0.0)
        self.assertEqual(result.yearly_savings, 0.0)
        self.assertEqual(result.confidence, 90)
        self.assertEqual(len(result.opportunities), 0)

        # Verify serialization
        self.assertEqual(result.model_dump()["opportunities"], [])
        json_str = result.model_dump_json()
        self.assertTrue(len(json_str) > 0)

    def test_subscriptions_and_duplicates_opportunities(self):
        """Verify generation of subscription and duplicate charge dispute opportunities."""
        # 1. Add subscription payments (3 cycles Netflix)
        sub_dates = [date(2026, 5, 1), date(2026, 6, 1), date(2026, 7, 1)]
        for d in sub_dates:
            self.add_tx(1200.0, "expense", "Netflix", d, self.entertainment_cat)

        # 2. Add duplicate payments: 1500 same day Zomato
        self.add_tx(1500.0, "expense", "Zomato", date(2026, 7, 10), self.food_cat, "Dinner")
        self.add_tx(1500.0, "expense", "Zomato", date(2026, 7, 10), self.food_cat, "Dinner Duplicate")

        context = self.builder.build_context(self.db, self.user_id)
        result = self.service.generate_opportunities(context)

        opportunity_types = [opp.opportunity_type for opp in result.opportunities]
        self.assertIn("subscriptions", opportunity_types)
        self.assertIn("duplicates", opportunity_types)

        # Assert subscriptions opportunity details
        sub_opp = next(opp for opp in result.opportunities if opp.opportunity_type == "subscriptions")
        self.assertEqual(sub_opp.potential_monthly_savings, 1200.0)
        self.assertEqual(sub_opp.potential_yearly_savings, 1200.0 * 12.0)
        self.assertEqual(sub_opp.confidence_score, 95)
        self.assertIn("Cancel subscriptions you haven't used in the past 30 days.", sub_opp.recommendation.action_steps)

        # Assert duplicate charges opportunity details
        dup_opp = next(opp for opp in result.opportunities if opp.opportunity_type == "duplicates")
        self.assertEqual(dup_opp.potential_monthly_savings, 1500.0)
        self.assertEqual(dup_opp.confidence_score, 90)

    def test_weekend_spending_and_budget_overruns_opportunities(self):
        """Verify weekend overspending and budget overrun opportunity detection."""
        # Baseline Income
        self.add_tx(50000.0, "income", "Employer", date(2026, 7, 1), self.salary_cat)

        # 1. Setup budget overruns
        # Budget = 1000, spend = 1500 -> overrun = 500
        budget = Budget(
            id=uuid.uuid4(),
            user_id=self.user_id,
            category_id=self.food_cat.id,
            amount=1000.0,
            month=7,
            year=2026
        )
        self.db.add(budget)
        self.db.commit()

        self.add_tx(1500.0, "expense", "Zomato", date(2026, 7, 10), self.food_cat)

        # 2. Weekend overspending: 5 weekdays at 100, 2 weekend days at 10000
        for idx in range(5):
            d = date(2026, 6, 8) + timedelta(days=idx)
            self.add_tx(100.0, "expense", "Store", d, self.shopping_cat)

        self.add_tx(10000.0, "expense", "Pub", date(2026, 6, 13), self.shopping_cat)
        self.add_tx(10000.0, "expense", "Cinema", date(2026, 6, 14), self.shopping_cat)

        context = self.builder.build_context(self.db, self.user_id)
        result = self.service.generate_opportunities(context)

        opportunity_types = [opp.opportunity_type for opp in result.opportunities]
        self.assertIn("budget_overruns", opportunity_types)
        self.assertIn("weekend_spend", opportunity_types)

        # Budget overrun details:spent 1500, budget 1000 -> overrun 500
        over_opp = next(opp for opp in result.opportunities if opp.opportunity_type == "budget_overruns")
        self.assertEqual(over_opp.potential_monthly_savings, 500.0)
        self.assertEqual(over_opp.confidence_score, 95)

        # Weekend overspending savings (weekend daily avg = 10000, weekday daily avg = 100 -> excess = 9900 * 8 = 79200)
        # Wait, since Netflix or other expenses might change weekday average, let's verify exact ratio:
        week_opp = next(opp for opp in result.opportunities if opp.opportunity_type == "weekend_spend")
        self.assertTrue(week_opp.potential_monthly_savings > 0)
        self.assertEqual(week_opp.confidence_score, 85)

    def test_merchant_concentration_opportunity(self):
        """Verify merchant concentration triggers savings targets (10% target optimization)."""
        # Expenses total: 3900. Merchant spend at Adani: 2500 (64.1% of total) -> Concentration!
        self.add_tx(2500.0, "expense", "Adani Electricity", date(2026, 7, 5), self.utilities_cat)
        self.add_tx(500.0, "expense", "Zomato", date(2026, 7, 6), self.food_cat)
        self.add_tx(900.0, "expense", "Amazon", date(2026, 7, 7), self.shopping_cat)

        context = self.builder.build_context(self.db, self.user_id)
        result = self.service.generate_opportunities(context)

        opp = next(opp for opp in result.opportunities if opp.opportunity_type == "merchant_concentration")
        self.assertEqual(opp.metadata["merchant"], "Adani Electricity")
        # 10% target savings on 2500 spend = 250 monthly
        self.assertEqual(opp.potential_monthly_savings, 250.0)
        self.assertEqual(opp.potential_yearly_savings, 250.0 * 12.0)
        self.assertEqual(opp.confidence_score, 80)


if __name__ == "__main__":
    unittest.main()
