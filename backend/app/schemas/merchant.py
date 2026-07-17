from pydantic import BaseModel, Field

class MerchantInfo(BaseModel):
    merchant: str = Field(..., description="Canonical merchant name")
    category: str = Field(..., description="Standardized category name")
    confidence: int = Field(..., description="Confidence score (0-100)")
