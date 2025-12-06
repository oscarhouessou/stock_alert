from pydantic import BaseModel
from typing import Optional, Literal, List

# Categories for products
CATEGORIES = ["alimentation", "vêtements", "cosmétiques", "autres"]
UNITS = ["Unité", "Kg", "Litre", "Carton", "Sac", "Paquet"]

class Product(BaseModel):
    id: Optional[int] = None
    name: str
    category: str = "autres"
    unit: str = "Unité"
    price: float = 0
    quantity: int = 0
    barcode: Optional[str] = None
    description: Optional[str] = None
    total_value: float = 0

class ProductInput(BaseModel):
    """Input for adding a product (from voice or form)"""
    name: str
    category: str = "autres"
    unit: str = "Unité"
    price: float = 0
    quantity: int = 0
    barcode: Optional[str] = None
    description: Optional[str] = None

class VoiceCommandResponse(BaseModel):
    original_text: str
    action: Literal["add", "remove", "check_stock", "check_value", "unknown"]
    products: List[ProductInput] = []  # Support multiple products
    message: str
