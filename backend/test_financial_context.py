import unittest
import uuid
import json
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.services.ai.financial_context_builder import FinancialContextBuilder


class TestFinancialContextBuilder(unittest.TestCase):
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

        # Create a checking account
        self.account_id = uuid.uuid4()
        self.account = Account(
            id=self.account_id,
            user_id=self.user_id,
            name="Checking Account",
            balance=15000.0,
            currency="INR",
            icon="Bank",
            color="#3b82f6"
        )
        self.db.add(self.account)
        self.db.commit()

        # Create categories
        self.salary_cat = self.create_category("Salary", "income")
        self.shopping_cat = self.create_category("Shopping", "expense")
        self.food_cat = self.create_category("Food Delivery", "expense")

        self.builder = FinancialContextBuilder()

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

    def test_empty_database_context(self):
        """Verify context builder executes correctly with zero transactions/budgets."""
        context = self.builder.build_context(self.db, self.user_id)
        
        self.assertEqual(context.profile.transaction_count, 0)
        self.assertEqual(context.profile.account_count, 1)
        self.assertEqual(context.income.total_income, 0.0)
        self.assertEqual(context.expenses.total_expenses, 0.0)
        self.assertEqual(context.categories.top_categories, [])
        self.assertEqual(context.merchants.top_merchants, [])
        self.assertEqual(context.subscriptions.active_subscriptions, [])
        
        # Verify serialization to dictionary and JSON string works cleanly
        dict_dump = context.model_dump()
        self.assertEqual(dict_dump["profile"]["transaction_count"], 0)
        json_str = context.model_dump_json()
        self.assertTrue(len(json_str) > 0)

    def test_full_context_calculation(self):
        """Verify context builder calculates averages, MoM changes, categories, merchants, and ratios."""
        # Current month: July 2026. Previous month: June 2026.
        # Income in July: 30000 (Salary)
        self.add_tx(30000.0, "income", "Tech Corp", date(2026, 7, 1), self.salary_cat, "Salary Credited")
        
        # Expenses in June: 5000 (Shopping)
        self.add_tx(5000.0, "expense", "Amazon", date(2026, 6, 15), self.shopping_cat, "Shopping purchase")

        # Expenses in July:
        # Zomato: 1000
        # Zomato: 1500 (Duplicate same day)
        self.add_tx(1000.0, "expense", "Zomato", date(2026, 7, 10), self.food_cat, "Dinner")
        self.add_tx(1000.0, "expense", "Zomato", date(2026, 7, 10), self.food_cat, "Dinner Duplicate")
        self.add_tx(1500.0, "expense", "Flipkart", date(2026, 7, 12), self.shopping_cat, "Flipkart purchase")

        # Set up a budget for Food Delivery in July = 1500. July spend = 2000 (1000+1000). Exceeded!
        budget = Budget(
            id=uuid.uuid4(),
            user_id=self.user_id,
            category_id=self.food_cat.id,
            amount=1500.0,
            month=7,
            year=2026
        )
        self.db.add(budget)
        self.db.commit()

        # Build context
        context = self.builder.build_context(self.db, self.user_id)

        # Assert Profile
        self.assertEqual(context.profile.transaction_count, 5)
        self.assertEqual(context.profile.current_month, "July 2026")
        self.assertEqual(context.profile.previous_month, "June 2026")

        # Assert Income
        self.assertEqual(context.income.total_income, 30000.0)
        self.assertEqual(context.income.monthly_income, 30000.0)

        # Assert Expenses
        self.assertEqual(context.expenses.total_expenses, 8500.0) # 5000 (June) + 3500 (July: 1000+1000+1500)
        self.assertEqual(context.expenses.monthly_expenses, 3500.0)
        self.assertEqual(context.expenses.previous_month_expenses, 5000.0)
        self.assertEqual(context.expenses.percentage_change, -30.0) # (3500-5000)/5000 * 100 = -30%
        self.assertEqual(context.expenses.largest_transaction, 5000.0)
        self.assertEqual(context.expenses.smallest_transaction, 1000.0)
        # Sorted expense amounts: [1000.0, 1000.0, 1500.0, 5000.0]. Median of 4 elements = (1000 + 1500)/2 = 1250!
        self.assertEqual(context.expenses.median_transaction, 1250.0)

        # Assert Categories
        top_cats = {c["category"]: c["amount"] for c in context.categories.top_categories}
        self.assertEqual(top_cats["Shopping"], 6500.0)
        self.assertEqual(top_cats["Food Delivery"], 2000.0)
        
        # Budget utilization for Food Delivery: spent 2000, budget 1500 -> utilization 133.33%
        food_util = next(b for b in context.categories.budget_utilization if b.category_name == "Food Delivery")
        self.assertEqual(food_util.spent_amount, 2000.0)
        self.assertEqual(food_util.utilization_pct, 133.33)
        self.assertTrue(food_util.is_exceeded)
        self.assertIn("Food Delivery", context.categories.exceeded_budgets)

        # Assert Merchants
        merchants_concentration = context.merchants.merchant_concentration
        self.assertEqual(merchants_concentration["Amazon"], round(5000.0 / 8500.0 * 100, 2))
        self.assertIn("Zomato", context.merchants.repeat_merchants)

        # Assert Rules findings collection
        findings_types = [f.rule_type for f in context.rules_engine]
        self.assertIn("duplicate_charge", findings_types)

        # Assert Health Context
        self.assertEqual(context.health.savings_rate, round((30000.0 - 3500.0) / 30000.0 * 100, 2))
        self.assertEqual(context.health.expense_ratio, round(3500.0 / 30000.0, 2))
        self.assertEqual(context.health.emergency_fund_months, round(15000.0 / 3500.0, 2))

        # Assert Savings Opportunities Context
        self.assertEqual(context.savings.duplicate_charges_total, 1000.0) # Zomato duplicate same day
        self.assertEqual(context.savings.budget_overrun_total, 500.0) # Food Delivery spent 2000 vs 1500 budget


if __name__ == "__main__":
    unittest.main()
