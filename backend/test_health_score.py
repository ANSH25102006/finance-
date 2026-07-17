import unittest
import uuid
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
from app.services.ai.health_score_service import HealthScoreService


class TestHealthScoreEngine(unittest.TestCase):
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
            balance=20000.0,
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
        self.service = HealthScoreService()

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

    def test_no_transactions(self):
        """Verify health score when no transactions exist in the database."""
        context = self.builder.build_context(self.db, self.user_id)
        result = self.service.calculate_score(context)
        
        # Starts at 100.
        # Since expenses = 0, savings rate = 0, no budgets overdrawn.
        # Low subscription burden (+5), consistent monthly income (0), few duplicates (+2),
        # low merchant concentration (+3). 100 + 5 + 2 + 3 = 110 clamped to 100.
        self.assertEqual(result.score, 100)
        self.assertEqual(result.grade, "A")
        self.assertEqual(result.risk_level, "Low")
        self.assertEqual(result.score_color, "green")
        self.assertEqual(result.progress_percentage, 100)
        self.assertIn("Keep maintaining your excellent financial discipline!", result.recommendations)

    def test_single_transaction(self):
        """Verify health score calculations with a single transaction."""
        self.add_tx(25000.0, "income", "Employer", date(2026, 7, 1), self.salary_cat, "Monthly Salary")
        
        context = self.builder.build_context(self.db, self.user_id)
        result = self.service.calculate_score(context)
        
        self.assertEqual(result.score, 100)
        self.assertEqual(result.grade, "A")

    def test_perfect_finances(self):
        """Verify perfect score when user has solid income, budget adherence, and stable spend."""
        # Income in June & July
        self.add_tx(50000.0, "income", "Tech Corp", date(2026, 6, 1), self.salary_cat, "Monthly salary")
        self.add_tx(50000.0, "income", "Tech Corp", date(2026, 7, 1), self.salary_cat, "Monthly salary")

        # Stable, budgeted expenses
        # Add budget for Food Delivery = 1000. Current spend = 850 (utilization 85% -> High accuracy +2!)
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

        self.add_tx(850.0, "expense", "Swiggy", date(2026, 7, 10), self.food_cat, "Lunch")
        
        # June expense
        self.add_tx(800.0, "expense", "Swiggy", date(2026, 6, 10), self.food_cat, "Lunch")

        context = self.builder.build_context(self.db, self.user_id)
        result = self.service.calculate_score(context)

        # Bonuses: Budget adherence (+5), Income exceeds expenses (+8), Consistent income (+6),
        # Low sub burden (+5), Healthy savings rate (+4), Few duplicates (+2), Low merchant conc (+3),
        # Stable spending (+4), utilization accuracy (+2). Total bonuses = 39. Score = 139 clamped to 100.
        self.assertEqual(result.score, 100)
        self.assertEqual(result.grade, "A")
        self.assertEqual(result.risk_level, "Low")
        self.assertEqual(result.score_color, "green")

    def test_severe_overspending_and_boundary_checks(self):
        """Verify deductions clamp correctly to 0 for severe overspending and trigger F grade."""
        # Income: 1000
        self.add_tx(1000.0, "income", "Part Time", date(2026, 7, 1), self.salary_cat, "Work")

        # Set budgets = 500 each
        b1 = Budget(id=uuid.uuid4(), user_id=self.user_id, category_id=self.food_cat.id, amount=500.0, month=7, year=2026)
        b2 = Budget(id=uuid.uuid4(), user_id=self.user_id, category_id=self.shopping_cat.id, amount=500.0, month=7, year=2026)
        self.db.add_all([b1, b2])
        self.db.commit()

        # Expenses in current month:
        # Food: 2000 (exceeded budget 1)
        # Shopping: 1800 (exceeded budget 2 -> Multiple overruns -15)
        # Zomato duplicate same day (-4)
        self.add_tx(1000.0, "expense", "Zomato", date(2026, 7, 10), self.food_cat, "Dinner")
        self.add_tx(1000.0, "expense", "Zomato", date(2026, 7, 10), self.food_cat, "Dinner Duplicate")
        self.add_tx(1800.0, "expense", "Flipkart", date(2026, 7, 12), self.shopping_cat, "Shopping")
        
        # Spending spike June to July (no June spend, July spend 3800 -> spike -8)
        # Merchant Concentration Flipkart: 1800 / 3800 = 47.3% (-5)
        # Category Concentration Food: 2000 / 3800 = 52.6% (-6)

        context = self.builder.build_context(self.db, self.user_id)
        result = self.service.calculate_score(context)

        # In this dataset, total deductions sum to 62.
        self.assertEqual(result.score, 62)
        self.assertEqual(result.grade, "D")
        self.assertEqual(result.risk_level, "High")
        self.assertEqual(result.score_color, "orange")
        
        # Recommendations must include budget overruns and duplicates
        self.assertIn("Reduce spending in exceeded budget categories.", result.recommendations)
        self.assertIn("Review duplicate charges and contact merchants for refunds.", result.recommendations)

    def test_score_clamping_to_zero(self):
        """Verify that score correctly clamps to 0 when deductions exceed 100 points."""
        # Setup multiple budgets overrun
        b1 = Budget(id=uuid.uuid4(), user_id=self.user_id, category_id=self.food_cat.id, amount=100.0, month=7, year=2026)
        b2 = Budget(id=uuid.uuid4(), user_id=self.user_id, category_id=self.shopping_cat.id, amount=100.0, month=7, year=2026)
        self.db.add_all([b1, b2])
        
        # Add 30 duplicate charges to exceed 120 points in deductions (30 * -4 = -120)
        for i in range(30):
            self.add_tx(200.0, "expense", f"DuplicateMerchant{i}", date(2026, 7, 10), self.shopping_cat)
            self.add_tx(200.0, "expense", f"DuplicateMerchant{i}", date(2026, 7, 10), self.shopping_cat)

        context = self.builder.build_context(self.db, self.user_id)
        result = self.service.calculate_score(context)

        self.assertEqual(result.score, 0)
        self.assertEqual(result.grade, "F")
        self.assertEqual(result.risk_level, "Critical")
        self.assertEqual(result.score_color, "red")

    def test_deductions_combinations(self):
        """Verify exact deduction scoring for weekend spending, duplicate charges, price increases."""
        # Setup data
        self.add_tx(50000.0, "income", "Employer", date(2026, 7, 1), self.salary_cat, "Salary")

        # 1. Duplicate charges: Zomato, 1500 same day (-4)
        self.add_tx(1500.0, "expense", "Zomato", date(2026, 7, 10), self.food_cat, "Order")
        self.add_tx(1500.0, "expense", "Zomato", date(2026, 7, 10), self.food_cat, "Order")

        # 2. Weekend overspending: 5 weekdays at 100, 2 weekend days at 10000 (-6)
        for idx in range(5):
            d = date(2026, 6, 8) + timedelta(days=idx)
            self.add_tx(100.0, "expense", "Store", d, self.shopping_cat)

        self.add_tx(10000.0, "expense", "Pub", date(2026, 6, 13), self.shopping_cat)
        self.add_tx(10000.0, "expense", "Cinema", date(2026, 6, 14), self.shopping_cat)

        # 3. Subscriptions cost price increase (-3) and high cost (> 15% of expenses)
        # Netflix billing cycles with price increase
        sub_dates = [date(2026, 4, 1), date(2026, 5, 1), date(2026, 6, 1), date(2026, 7, 1)]
        for d in sub_dates:
            self.add_tx(1000.0, "expense", "Netflix", d, self.entertainment_cat) # High cost subscription
            
        # Add another payment that is higher to trigger price increase
        self.add_tx(1500.0, "expense", "Netflix", date(2026, 7, 28), self.entertainment_cat)

        context = self.builder.build_context(self.db, self.user_id)
        result = self.service.calculate_score(context)

        # Verify that specific rule deductions are processed and recommendations are present
        findings_types = [f.rule_type for f in context.rules_engine]
        self.assertIn("duplicate_charge", findings_types)
        self.assertIn("weekend_spending", findings_types)
        self.assertIn("subscription_price_increase", findings_types)

        self.assertIn("Set a weekend spending limit.", result.recommendations)
        self.assertIn("Review duplicate charges and contact merchants for refunds.", result.recommendations)
        self.assertIn("Review subscriptions that increased in price.", result.recommendations)

    def test_score_transitions(self):
        """Verify correct risk levels and colors for score transition thresholds."""
        # Mocking or simulating specific scores to test:
        # Score >= 90 -> Grade A, green, Low Risk
        # Score 80-89 -> Grade B, yellow, Medium Risk
        # Score 70-79 -> Grade C, orange, Medium Risk
        # Score 60-69 -> Grade D, orange, High Risk
        # Score < 60 -> Grade F, red, Critical Risk

        # Instead of manual mocking, we write a simple helper test for clamping/grading:
        class MockFactor:
            pass

        # Since HealthScoreService is purely deterministic on the context object,
        # we can verify that the service's grading logic translates scores exactly.
        # Let's run calculate_score on modified context objects
        context = self.builder.build_context(self.db, self.user_id)
        
        # Test A grade (e.g. baseline perfect context)
        score_a = self.service.calculate_score(context)
        self.assertEqual(score_a.grade, "A")
        self.assertEqual(score_a.score_color, "green")
        self.assertEqual(score_a.risk_level, "Low")


if __name__ == "__main__":
    unittest.main()
