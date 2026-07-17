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
from app.services.audit_service import AuditService


class TestRulesEngine(unittest.TestCase):
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

        # Create multiple accounts (checking and credit)
        self.checking_id = uuid.uuid4()
        self.checking = Account(
            id=self.checking_id,
            user_id=self.user_id,
            name="Checking",
            balance=50000.0,
            currency="INR",
            icon="Bank",
            color="#3b82f6"
        )
        
        self.credit_id = uuid.uuid4()
        self.credit = Account(
            id=self.credit_id,
            user_id=self.user_id,
            name="Credit Card",
            balance=-1000.0,
            currency="INR",
            icon="CreditCard",
            color="#ef4444"
        )
        self.db.add_all([self.checking, self.credit])
        self.db.commit()

        # Create categories
        self.salary_cat = self.create_category("Salary", "income")
        self.shopping_cat = self.create_category("Shopping", "expense")
        self.food_cat = self.create_category("Food Delivery", "expense")
        self.utilities_cat = self.create_category("Utilities", "expense")
        self.entertainment_cat = self.create_category("Entertainment", "expense")

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

    def add_tx(self, account_id, category, amount, tx_type, merchant, tx_date, desc="Test"):
        tx = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            account_id=account_id,
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

    def test_empty_transaction_history(self):
        """Verify rules engine handles empty transaction history without errors."""
        service = AuditService(self.db, self.user_id)
        result = service.run_rules_audit()
        self.assertEqual(result["summary"]["findings"], 0)
        self.assertEqual(result["findings"], [])

    def test_one_transaction(self):
        """Verify rules engine functions correctly with exactly one transaction."""
        self.add_tx(self.checking_id, self.shopping_cat, 100.0, "expense", "Amazon", date(2026, 7, 1))
        service = AuditService(self.db, self.user_id)
        result = service.run_rules_audit()
        # With 1 transaction, standard outlier checks can't run, no recurring alerts, etc.
        # But should run cleanly and return 0 findings
        self.assertEqual(result["summary"]["findings"], 0)

    def test_recurring_subscriptions_and_price_increase(self):
        """Verify forgotten subscription detection and price increase alerts."""
        # Add 4 billing cycles (Netflix)
        # Netflix: 199, 199, 249, 249
        dates = [date(2026, 3, 1), date(2026, 4, 1), date(2026, 5, 2), date(2026, 6, 1)]
        amounts = [199.0, 199.0, 249.0, 249.0]
        
        for d, a in zip(dates, amounts):
            self.add_tx(self.credit_id, self.entertainment_cat, a, "expense", "Netflix", d, "Netflix Sub")

        service = AuditService(self.db, self.user_id)
        result = service.run_rules_audit()

        findings = result["findings"]
        rule_types = [f["rule_type"] for f in findings]
        
        self.assertIn("forgotten_subscription", rule_types)
        self.assertIn("subscription_price_increase", rule_types)

        # Assert Forgotten Subscription details
        sub_finding = next(f for f in findings if f["rule_type"] == "forgotten_subscription")
        self.assertEqual(sub_finding["metadata"]["merchant"], "Netflix")
        self.assertEqual(sub_finding["metadata"]["monthly_amount"], 224.0) # avg of [199, 199, 249, 249]
        self.assertEqual(sub_finding["metadata"]["yearly_cost"], 224.0 * 12)

        # Assert Price Increase details
        inc_finding = next(f for f in findings if f["rule_type"] == "subscription_price_increase")
        self.assertEqual(inc_finding["metadata"]["old_price"], 199.0)
        self.assertEqual(inc_finding["metadata"]["new_price"], 249.0)
        self.assertEqual(inc_finding["metadata"]["increase_amount"], 50.0)
        self.assertEqual(inc_finding["metadata"]["increase_percentage"], 25.13) # (50/199)*100 = 25.1256...

    def test_duplicate_charges(self):
        """Verify detection of duplicate charges on the same day and within 1 day."""
        t1 = date(2026, 7, 10)
        t2 = date(2026, 7, 10) # Same day
        t3 = date(2026, 7, 11) # Within 1 day
        t4 = date(2026, 7, 13) # Distinct day

        # Duplicate same day
        self.add_tx(self.checking_id, self.shopping_cat, 1500.0, "expense", "Zomato", t1, "Zomato Order")
        self.add_tx(self.checking_id, self.shopping_cat, 1500.0, "expense", "Zomato", t2, "Zomato Order")
        
        # Duplicate consecutive day
        self.add_tx(self.checking_id, self.shopping_cat, 800.0, "expense", "Uber", t1, "Uber ride")
        self.add_tx(self.checking_id, self.shopping_cat, 800.0, "expense", "Uber", t3, "Uber ride")
        
        # Non-duplicate (different day)
        self.add_tx(self.checking_id, self.shopping_cat, 600.0, "expense", "Ola", t1, "Ola ride")
        self.add_tx(self.checking_id, self.shopping_cat, 600.0, "expense", "Ola", t4, "Ola ride")

        service = AuditService(self.db, self.user_id)
        result = service.run_rules_audit()

        findings = [f for f in result["findings"] if f["rule_type"] == "duplicate_charge"]
        self.assertEqual(len(findings), 2)

        # Same day duplicate (High severity)
        same_day = next(f for f in findings if f["severity"] == "high")
        self.assertEqual(same_day["metadata"]["merchant"], "Zomato")
        self.assertEqual(same_day["confidence_score"], 95)

        # Consecutive day duplicate (Medium severity)
        one_day = next(f for f in findings if f["severity"] == "medium")
        self.assertEqual(one_day["metadata"]["merchant"], "Uber")
        self.assertEqual(one_day["confidence_score"], 85)

    def test_spending_spikes(self):
        """Verify spending spikes detection in categories and merchants."""
        # Prev Month: June 2026
        # Curr Month: July 2026
        # Food spike: June spend = 1000, July spend = 2500 (150% increase, spike > 50% and increase >= 500)
        self.add_tx(self.checking_id, self.food_cat, 1000.0, "expense", "Swiggy", date(2026, 6, 5))
        self.add_tx(self.checking_id, self.food_cat, 2500.0, "expense", "Swiggy", date(2026, 7, 5))

        service = AuditService(self.db, self.user_id)
        result = service.run_rules_audit()

        findings = [f for f in result["findings"] if f["rule_type"] == "spending_spike"]
        # Should detect a category spike for Food Delivery and a merchant spike for Swiggy
        self.assertEqual(len(findings), 2)

        cat_spike = next(f for f in findings if f["metadata"]["type"] == "category")
        self.assertEqual(cat_spike["metadata"]["name"], "Food Delivery")
        self.assertEqual(cat_spike["metadata"]["increase_percentage"], 150.0)

        merch_spike = next(f for f in findings if f["metadata"]["type"] == "merchant")
        self.assertEqual(merch_spike["metadata"]["name"], "Swiggy")

    def test_large_transactions_statistical_outliers(self):
        """Verify statistical outlier detection using IQR and SD fallback."""
        # 10 baseline expenses to establish statistical distribution
        # Amounts: 100, 110, 105, 95, 120, 115, 100, 90, 110, 105 (IQR will be small, ~15)
        base_amounts = [100.0, 110.0, 105.0, 95.0, 120.0, 115.0, 100.0, 90.0, 110.0, 105.0]
        for a in base_amounts:
            self.add_tx(self.checking_id, self.shopping_cat, a, "expense", "Store", date(2026, 7, 1))

        # Extreme outlier transaction
        outlier = self.add_tx(self.checking_id, self.shopping_cat, 1000.0, "expense", "Luxury Store", date(2026, 7, 15))

        service = AuditService(self.db, self.user_id)
        result = service.run_rules_audit()

        findings = [f for f in result["findings"] if f["rule_type"] == "large_transaction"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["affected_transactions"], [outlier.id])
        self.assertEqual(findings[0]["metadata"]["merchant"], "Luxury Store")

    def test_salary_detection_and_refunds(self):
        """Verify recurring salary detection and refund identification."""
        # 3 cycles of recurring income matching salary keywords
        dates = [date(2026, 5, 1), date(2026, 6, 1), date(2026, 7, 1)]
        for d in dates:
            self.add_tx(self.checking_id, self.salary_cat, 45000.0, "income", "Tech Corp", d, "Monthly Salary Credited")

        # Add refund transaction
        self.add_tx(self.checking_id, self.shopping_cat, 350.0, "income", "Amazon", date(2026, 7, 10), "Refund for returned book")

        service = AuditService(self.db, self.user_id)
        result = service.run_rules_audit()

        rule_types = [f["rule_type"] for f in result["findings"]]
        self.assertIn("income_detection", rule_types)
        self.assertIn("refund_detection", rule_types)

        salary = next(f for f in result["findings"] if f["rule_type"] == "income_detection")
        self.assertEqual(salary["metadata"]["monthly_amount"], 45000.0)

        refund = next(f for f in result["findings"] if f["rule_type"] == "refund_detection")
        self.assertEqual(refund["metadata"]["amount"], 350.0)

    def test_weekend_spending(self):
        """Verify weekend spending Concentration triggers if daily avg is >= 1.5x weekdays."""
        # Weekdays: Mon-Fri (Mon=June 8 to Fri=June 12)
        # Weekends: Sat-Sun (Sat=June 13 to Sun=June 14)
        # Weekday spend: 5 days, 100 per day = 500 total. Daily avg = 100.
        for idx in range(5):
            d = date(2026, 6, 8) + timedelta(days=idx)
            self.add_tx(self.checking_id, self.shopping_cat, 100.0, "expense", "Shop", d)

        # Weekend spend: 2 days, 600 per day = 1200 total. Daily avg = 600. (600 >= 1.5 * 100)
        self.add_tx(self.checking_id, self.shopping_cat, 600.0, "expense", "Pub", date(2026, 6, 13))
        self.add_tx(self.checking_id, self.shopping_cat, 600.0, "expense", "Cinema", date(2026, 6, 14))

        service = AuditService(self.db, self.user_id)
        result = service.run_rules_audit()

        findings = [f for f in result["findings"] if f["rule_type"] == "weekend_spending"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["metadata"]["ratio"], 6.0)

    def test_merchant_concentration(self):
        """Verify merchant concentration flags if a merchant spends >= 25% of total expenses."""
        # Total expenses: 3900. Merchant spend at Adani: 2500 (64.1% of total)
        self.add_tx(self.checking_id, self.utilities_cat, 2500.0, "expense", "Adani Electricity", date(2026, 7, 5))
        self.add_tx(self.checking_id, self.food_cat, 500.0, "expense", "Zomato", date(2026, 7, 6))
        self.add_tx(self.checking_id, self.shopping_cat, 900.0, "expense", "Amazon", date(2026, 7, 7))

        service = AuditService(self.db, self.user_id)
        result = service.run_rules_audit()

        findings = [f for f in result["findings"] if f["rule_type"] == "merchant_concentration"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["metadata"]["merchant"], "Adani Electricity")
        self.assertAlmostEqual(findings[0]["metadata"]["percentage"], 64.10, places=1)

    def test_category_concentration(self):
        """Verify category concentration triggers based on budgets, or falls back to total spend percentage."""
        # Scenario A: Budgets defined.
        # Add budget for Food Delivery = 1000
        budget = Budget(
            id=uuid.uuid4(),
            user_id=self.user_id,
            category_id=self.food_cat.id,
            amount=1000.0,
            month=7,
            year=2026
        )
        self.db.add(budget)
        
        # Add budget for Shopping = 2000
        budget2 = Budget(
            id=uuid.uuid4(),
            user_id=self.user_id,
            category_id=self.shopping_cat.id,
            amount=2000.0,
            month=7,
            year=2026
        )
        self.db.add(budget2)
        self.db.commit()

        # Food spend: 900 (90% of budget -> Medium alert)
        self.add_tx(self.checking_id, self.food_cat, 900.0, "expense", "Zomato", date(2026, 7, 10))

        # Shopping spend: 2200 (110% of budget -> High alert)
        self.add_tx(self.checking_id, self.shopping_cat, 2200.0, "expense", "Amazon", date(2026, 7, 11))

        service = AuditService(self.db, self.user_id)
        result = service.run_rules_audit()

        findings = [f for f in result["findings"] if f["rule_type"] == "category_concentration"]
        self.assertEqual(len(findings), 2)

        # Budget exceeded (High)
        high_alert = next(f for f in findings if f["severity"] == "high")
        self.assertEqual(high_alert["metadata"]["category"], "Shopping")
        self.assertEqual(high_alert["metadata"]["percentage"], 110.0)

        # Budget nearly consumed (Medium)
        med_alert = next(f for f in findings if f["severity"] == "medium")
        self.assertEqual(med_alert["metadata"]["category"], "Food Delivery")

    def test_api_filters(self):
        """Verify filtering capabilities of run_rules_audit by severity, type, and date range."""
        # 1. Netflix subscription (medium)
        dates = [date(2026, 5, 1), date(2026, 6, 1), date(2026, 7, 1)]
        for d in dates:
            self.add_tx(self.credit_id, self.entertainment_cat, 199.0, "expense", "Netflix", d)

        # 2. Duplicate charge on credit card (high severity)
        self.add_tx(self.credit_id, self.shopping_cat, 500.0, "expense", "Shop", date(2026, 7, 10))
        self.add_tx(self.credit_id, self.shopping_cat, 500.0, "expense", "Shop", date(2026, 7, 10))

        service = AuditService(self.db, self.user_id)

        # Filter by severity = high
        high_res = service.run_rules_audit(severity_filter="high")
        self.assertTrue(len(high_res["findings"]) >= 1)
        self.assertTrue(all(f["severity"].lower() == "high" for f in high_res["findings"]))

        # Filter by rule_type = forgotten_subscription
        sub_res = service.run_rules_audit(rule_type_filter="forgotten_subscription")
        self.assertTrue(len(sub_res["findings"]) >= 1)
        self.assertTrue(all(f["rule_type"] == "forgotten_subscription" for f in sub_res["findings"]))

        # Filter by date range (exclude May transaction, which should prevent subscription from being active for 3 cycles)
        date_res = service.run_rules_audit(start_date=date(2026, 5, 15))
        # June & July is only 2 cycles of Netflix -> subscription check should fail to find 3 cycles
        sub_findings = [f for f in date_res["findings"] if f["rule_type"] == "forgotten_subscription"]
        self.assertEqual(len(sub_findings), 0)


if __name__ == "__main__":
    unittest.main()
