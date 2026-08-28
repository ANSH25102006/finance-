from typing import Dict, Any
from app.services.merchant.merchant_matcher import MerchantMatcher
from app.services.merchant.category_engine import CategoryEngine

class MerchantService:
    def __init__(self):
        self.matcher = MerchantMatcher()

    def recognize(self, description: str, db=None, user_id=None) -> Dict[str, Any]:
        """
        Recognize merchant name, standard category, and confidence score
        from a raw transaction description.
        Returns a dictionary with keys: 'merchant', 'category', 'confidence'.
        """
        if db and user_id:
            from app.models.merchant_mapping import UserMerchantMapping
            from app.services.merchant.confidence import Confidence
            # Check user mappings first
            mapping = db.query(UserMerchantMapping).filter(
                UserMerchantMapping.user_id == user_id,
                UserMerchantMapping.raw_name == description
            ).first()

            if mapping:
                return {
                    "merchant": mapping.normalized_name,
                    "category": mapping.category.name if mapping.category else "Uncategorized",
                    "confidence": Confidence.EXACT_ALIAS
                }
        merchant_name, merchant_cat, confidence = self.matcher.match(description)

        # Categorize the description with helper fallbacks if merchant is unknown
        category = CategoryEngine.determine_category(description, merchant_cat)

        return {
            "merchant": merchant_name,
            "category": category,
            "confidence": confidence
        }

    def learn_merchant(self, db, user_id, raw_name: str, normalized_name: str, category_id=None):
        """Persist a user-confirmed merchant mapping."""
        from app.models.merchant_mapping import UserMerchantMapping

        # Check if exists
        existing = db.query(UserMerchantMapping).filter(
            UserMerchantMapping.user_id == user_id,
            UserMerchantMapping.raw_name == raw_name
        ).first()

        if existing:
            existing.normalized_name = normalized_name
            existing.category_id = category_id
        else:
            new_map = UserMerchantMapping(
                user_id=user_id,
                raw_name=raw_name,
                normalized_name=normalized_name,
                category_id=category_id
            )
            db.add(new_map)
        db.commit()
