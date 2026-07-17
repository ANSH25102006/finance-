from typing import Dict, Any
from app.services.merchant.merchant_matcher import MerchantMatcher
from app.services.merchant.category_engine import CategoryEngine

class MerchantService:
    def __init__(self):
        self.matcher = MerchantMatcher()

    def recognize(self, description: str) -> Dict[str, Any]:
        """
        Recognize merchant name, standard category, and confidence score
        from a raw transaction description.
        Returns a dictionary with keys: 'merchant', 'category', 'confidence'.
        """
        merchant_name, merchant_cat, confidence = self.matcher.match(description)
        
        # Categorize the description with helper fallbacks if merchant is unknown
        category = CategoryEngine.determine_category(description, merchant_cat)

        return {
            "merchant": merchant_name,
            "category": category,
            "confidence": confidence
        }
