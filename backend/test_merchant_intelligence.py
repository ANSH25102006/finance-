import unittest
from unittest.mock import patch

from app.services.merchant.merchant_normalizer import normalize_description
from app.services.merchant.confidence import Confidence
from app.services.merchant.category_engine import CategoryEngine
from app.services.merchant.merchant_matcher import MerchantMatcher
from app.services.merchant.merchant_service import MerchantService
from app.services.merchant.merchant_database import MerchantDatabase


class TestMerchantIntelligence(unittest.TestCase):
    def setUp(self):
        # Initialize MerchantService which uses MerchantMatcher singleton
        self.service = MerchantService()

    def test_whitespace_normalization(self):
        """Verify normalization removes extra spaces, leading/trailing spaces."""
        self.assertEqual(normalize_description("  swiggy   order  "), "swiggy order")
        self.assertEqual(normalize_description("\tswiggy\norder\r"), "swiggy order")

    def test_case_insensitivity(self):
        """Verify merchant matching is case insensitive."""
        res_upper = self.service.recognize("SWIGGY ORDER")
        res_lower = self.service.recognize("swiggy order")
        res_mixed = self.service.recognize("SwIgGy OrDeR")

        self.assertEqual(res_upper["merchant"], "Swiggy")
        self.assertEqual(res_lower["merchant"], "Swiggy")
        self.assertEqual(res_mixed["merchant"], "Swiggy")

    def test_alias_matching(self):
        """Verify matching using simple aliases."""
        # 'amzn' is an alias of Amazon
        res = self.service.recognize("AMZN MKTPLACE PMTS")
        self.assertEqual(res["merchant"], "Amazon")
        self.assertEqual(res["category"], "Shopping")
        self.assertEqual(res["confidence"], Confidence.STRONG_ALIAS)  # 95

    def test_regex_matching(self):
        """Verify matching using regex aliases."""
        # Create a mock catalog containing a regex pattern to verify regex matching
        mock_catalog = [
            {
                "canonical_name": "MockRegexCorp",
                "aliases": ["^corp .* service$"],
                "category": "Utilities"
            }
        ]
        with patch.object(MerchantDatabase, 'get_merchants', return_value=mock_catalog):
            # Reset matcher singleton for mock injection
            MerchantMatcher._instance = None
            matcher = MerchantMatcher()
            
            # Match matching description (normalized to 'corp water service')
            m, c, conf = matcher.match("corp-water-service")
            self.assertEqual(m, "MockRegexCorp")
            self.assertEqual(c, "Utilities")
            self.assertEqual(conf, Confidence.STRONG_ALIAS)  # 95

            # Non-matching description
            m2, c2, conf2 = matcher.match("corp-water-services")
            self.assertEqual(m2, "Unknown")
            self.assertEqual(conf2, Confidence.UNKNOWN)  # 20

        # Reset matcher singleton back to normal
        MerchantMatcher._instance = None

    def test_unknown_merchants(self):
        """Verify matching unknown merchants returns 'Unknown' and low confidence."""
        res = self.service.recognize("XYZ SERVICES PVT LTD")
        self.assertEqual(res["merchant"], "Unknown")
        self.assertEqual(res["category"], "Unknown")
        self.assertEqual(res["confidence"], Confidence.UNKNOWN)  # 20

    def test_category_assignment(self):
        """Verify category assignment for merchants and fallback keywords."""
        # Merchant category mapping
        self.assertEqual(self.service.recognize("Swiggy Delivery")["category"], "Food Delivery")
        self.assertEqual(self.service.recognize("Uber Trip")["category"], "Transport")
        self.assertEqual(self.service.recognize("Netflix Subscription")["category"], "Entertainment")

        # Fallback keyword rules (Salary, Transfer)
        self.assertEqual(self.service.recognize("Monthly Salary Credited")["category"], "Salary")
        self.assertEqual(self.service.recognize("Self Transfer Savings")["category"], "Transfer")
        self.assertEqual(self.service.recognize("NEFT transfer description")["category"], "Transfer")
        self.assertEqual(self.service.recognize("Random details")["category"], "Unknown")

    def test_confidence_calculation(self):
        """Verify confidence calculations for different match qualities."""
        # 100: Exact alias match
        self.assertEqual(self.service.recognize("Swiggy")["confidence"], Confidence.EXACT_ALIAS)

        # 99: Prefix / starts with canonical name
        self.assertEqual(self.service.recognize("Swiggy Food")["confidence"], Confidence.PREFIX_MATCH)

        # 95: Strong alias / prefix match with alias
        self.assertEqual(self.service.recognize("AMZN MKTPLACE PMTS")["confidence"], Confidence.STRONG_ALIAS)

        # 80: Substring match
        # If "spotify" is in the middle of description: "monthly spotify premium"
        self.assertEqual(self.service.recognize("monthly spotify premium")["confidence"], Confidence.SUBSTRING)

        # 20: Unknown
        self.assertEqual(self.service.recognize("unknown shop")["confidence"], Confidence.UNKNOWN)

    def test_mixed_descriptions(self):
        """Verify handling of complex descriptions containing UPI prefixes, numbers, reference IDs."""
        # Input: UPI/12345/SWIGGY ORDER
        res = self.service.recognize("UPI/12345/SWIGGY ORDER")
        self.assertEqual(res["merchant"], "Swiggy")
        self.assertEqual(res["category"], "Food Delivery")
        self.assertEqual(res["confidence"], Confidence.PREFIX_MATCH)  # 99

        # Input: IMPS/Ref:987654/Uber Ride/Charge
        res2 = self.service.recognize("IMPS/Ref:987654/Uber Ride/Charge")
        self.assertEqual(res2["merchant"], "Uber")
        self.assertEqual(res2["category"], "Transport")
        self.assertEqual(res2["confidence"], Confidence.PREFIX_MATCH)

    def test_duplicate_aliases(self):
        """Verify that duplicate aliases in catalog configuration do not cause crashes."""
        mock_catalog = [
            {
                "canonical_name": "Swiggy",
                "aliases": ["swiggy", "duplicate_alias"],
                "category": "Food Delivery"
            },
            {
                "canonical_name": "Swiggy Extra",
                "aliases": ["duplicate_alias"],
                "category": "Food Delivery"
            }
        ]
        with patch.object(MerchantDatabase, 'get_merchants', return_value=mock_catalog):
            # Reset matcher singleton for mock injection
            MerchantMatcher._instance = None
            matcher = MerchantMatcher()

            # Should initialize cleanly and be able to resolve
            m, c, conf = matcher.match("duplicate_alias")
            self.assertIn(m, ["Swiggy", "Swiggy Extra"])  # Resolved to one of the matches
            self.assertEqual(conf, Confidence.EXACT_ALIAS)

        # Reset matcher singleton back to normal
        MerchantMatcher._instance = None


if __name__ == "__main__":
    unittest.main()
