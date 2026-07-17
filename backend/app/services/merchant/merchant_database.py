import json
import os
from typing import List, Dict, Any

class MerchantDatabase:
    _catalog: List[Dict[str, Any]] = []

    @classmethod
    def load_catalog(cls) -> List[Dict[str, Any]]:
        """
        Reads the configurable merchant catalog JSON and caches it in memory.
        """
        if cls._catalog:
            return cls._catalog

        dir_path = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(dir_path, "merchant_catalog.json")

        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    cls._catalog = json.load(f)
            except Exception:
                cls._catalog = []
        else:
            cls._catalog = []

        return cls._catalog

    @classmethod
    def get_merchants(cls) -> List[Dict[str, Any]]:
        """
        Returns the list of merchants in the catalog.
        """
        return cls.load_catalog()
