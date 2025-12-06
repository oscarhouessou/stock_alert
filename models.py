from pydantic import BaseModel, Field
from typing import Optional, Literal, List

# Categories for products
CATEGORIES = ["alimentation", "vêtements", "cosmétiques", "autres"]
UNITS = ["Unité", "Kg", "Litre", "Carton", "Sac", "Paquet"]

class Product(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier of the product")
    name: str = Field(..., description="Name of the product", example="Riz Parfum")
    category: str = Field("autres", description=f"Category from {CATEGORIES}", example="alimentation")
    unit: str = Field("Unité", description=f"Unit from {UNITS}", example="Sac")
    price: float = Field(0, description="Unit price in FCFA", example=12500)
    quantity: int = Field(0, description="Current stock quantity", example=50)
    barcode: Optional[str] = Field(None, description="Scanned barcode", example="123456789")
    description: Optional[str] = Field(None, description="Additional details", example="Sac de 50kg")
    total_value: float = Field(0, description="Calculated total value (price * quantity)")

class ProductInput(BaseModel):
    """Input for adding a product (from voice or form)"""
    name: str = Field(..., description="Name of the product", example="Riz Parfum")
    category: str = Field("autres", description=f"Category from {CATEGORIES}", example="alimentation")
    unit: str = Field("Unité", description=f"Unit from {UNITS}", example="Sac")
    price: float = Field(0, description="Unit price in FCFA", example=12500)
    quantity: int = Field(0, description="Quantity to add/update", example=10)
    barcode: Optional[str] = Field(None, description="Scanned barcode")
    description: Optional[str] = Field(None, description="Additional details")

class VoiceCommandResponse(BaseModel):
    original_text: str = Field(..., description="Transcribed text from audio")
    action: Literal["add", "remove", "check_stock", "check_value", "unknown"] = Field(..., description="Detected intent")
    products: List[ProductInput] = Field([], description="List of products extracted from command")
    message: str = Field(..., description="Human readable response message")
