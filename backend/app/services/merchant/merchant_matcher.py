import re
from typing import Dict, Any, Tuple, List
from app.services.merchant.merchant_database import MerchantDatabase
from app.services.merchant.merchant_normalizer import normalize_description
from app.services.merchant.confidence import Confidence

class MerchantMatcher:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MerchantMatcher, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        # Load configurable merchants catalog
        self.merchants = MerchantDatabase.get_merchants()
        self._prepare_matcher()
        self._initialized = True

    def _prepare_matcher(self):
        self.exact_matches: Dict[str, Dict[str, Any]] = {}
        self.prefix_matches: List[Tuple[str, Dict[str, Any]]] = []
        self.substring_matches: List[Tuple[str, Dict[str, Any]]] = []
        self.regex_matches: List[Tuple[re.Pattern, Dict[str, Any]]] = []

        # Process standard and configured merchants
        for m in self.merchants:
            canonical_lower = m["canonical_name"].lower().strip()
            
            # Map canonical name to exact matches
            self.exact_matches[canonical_lower] = m
            # Prefix matches
            self.prefix_matches.append((canonical_lower, m))
            # Substring matches
            self.substring_matches.append((canonical_lower, m))

            # Process aliases
            for alias in m.get("aliases", []):
                alias_lower = alias.lower().strip()
                if not alias_lower:
                    continue

                # Check if alias looks like a regex pattern (contains special regex chars)
                if any(char in alias_lower for char in [".*", "+", "^", "$", "(", ")", "[", "]"]):
                    try:
                        pattern = re.compile(alias_lower, re.IGNORECASE)
                        self.regex_matches.append((pattern, m))
                    except re.error:
                        # Fallback to substring match if regex is invalid
                        self.substring_matches.append((alias_lower, m))
                else:
                    self.exact_matches[alias_lower] = m
                    self.prefix_matches.append((alias_lower, m))
                    self.substring_matches.append((alias_lower, m))

    def match(self, description: str) -> Tuple[str, str, int]:
        """
        Match normalized transaction description to a merchant in the catalog.
        Returns: Tuple[merchant_canonical_name, category_name, confidence_score]
        """
        normalized = normalize_description(description)
        if not normalized:
            return "Unknown", "Unknown", Confidence.UNKNOWN

        raw_lower = description.lower().strip()

        # Helper to check if normalized starts with canonical name on word boundary
        def starts_with_canonical(m: Dict[str, Any]) -> bool:
            canonical_lower = m["canonical_name"].lower().strip()
            return normalized.startswith(canonical_lower) and (
                len(normalized) == len(canonical_lower) or normalized[len(canonical_lower)] == ' '
            )

        # Helper to check if substring matches on word boundaries
        def is_word_boundary_match(text: str, substring: str) -> bool:
            idx = text.find(substring)
            if idx == -1:
                return False
            # Check character before
            if idx > 0 and text[idx - 1].isalnum():
                return False
            # Check character after
            end_idx = idx + len(substring)
            if end_idx < len(text) and text[end_idx].isalnum():
                return False
            return True

        # Helper to check if it's an exact raw match
        def is_exact_raw_match(m: Dict[str, Any]) -> bool:
            if raw_lower == m["canonical_name"].lower().strip():
                return True
            for alias in m.get("aliases", []):
                if raw_lower == alias.lower().strip():
                    return True
            return False

        # 1. Exact Match (100)
        if normalized in self.exact_matches:
            match = self.exact_matches[normalized]
            if is_exact_raw_match(match):
                return match["canonical_name"], match["category"], Confidence.EXACT_ALIAS
            elif starts_with_canonical(match):
                return match["canonical_name"], match["category"], Confidence.PREFIX_MATCH
            return match["canonical_name"], match["category"], Confidence.STRONG_ALIAS

        # 2. Prefix Match (99 for starting with canonical name, 95 for starting with alias)
        sorted_prefixes = sorted(self.prefix_matches, key=lambda x: len(x[0]), reverse=True)
        for alias, match in sorted_prefixes:
            if normalized.startswith(alias):
                # Ensure word boundary match
                if len(normalized) == len(alias) or normalized[len(alias)] == ' ':
                    if is_exact_raw_match(match):
                        return match["canonical_name"], match["category"], Confidence.EXACT_ALIAS
                    if starts_with_canonical(match):
                        return match["canonical_name"], match["category"], Confidence.PREFIX_MATCH
                    return match["canonical_name"], match["category"], Confidence.STRONG_ALIAS

        # 3. Regex matches (95)
        for pattern, match in self.regex_matches:
            if pattern.search(normalized):
                if is_exact_raw_match(match):
                    return match["canonical_name"], match["category"], Confidence.EXACT_ALIAS
                if starts_with_canonical(match):
                    return match["canonical_name"], match["category"], Confidence.PREFIX_MATCH
                return match["canonical_name"], match["category"], Confidence.STRONG_ALIAS

        # 4. Substring matches (80)
        sorted_substrings = sorted(self.substring_matches, key=lambda x: len(x[0]), reverse=True)
        for alias, match in sorted_substrings:
            if alias in normalized and is_word_boundary_match(normalized, alias):
                if is_exact_raw_match(match):
                    return match["canonical_name"], match["category"], Confidence.EXACT_ALIAS
                if starts_with_canonical(match):
                    return match["canonical_name"], match["category"], Confidence.PREFIX_MATCH
                return match["canonical_name"], match["category"], Confidence.SUBSTRING

        # 5. Fallback
        return "Unknown", "Unknown", Confidence.UNKNOWN
