class CategoryEngine:
    VALID_CATEGORIES = {
        "Food Delivery",
        "Shopping",
        "Transport",
        "Entertainment",
        "Healthcare",
        "Utilities",
        "Telecom",
        "Payments",
        "Salary",
        "Transfer",
        "Unknown"
    }

    @classmethod
    def determine_category(cls, description: str, merchant_category: str = None) -> str:
        """
        Determines the category based on the recognized merchant's category or fallback keyword rules.
        """
        if merchant_category and merchant_category != "Unknown" and merchant_category in cls.VALID_CATEGORIES:
            return merchant_category

        desc_lower = description.lower()

        # Rule-based fallback keywords
        if any(w in desc_lower for w in ["salary", "payroll", "stipend", "wages"]):
            return "Salary"
        if any(w in desc_lower for w in ["transfer", "self transfer", "to a/c", "from a/c", "neft", "rtgs", "imps"]):
            return "Transfer"

        return "Unknown"
