"""Pydantic data models for the bot."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ReceiptItem(BaseModel):
    """Single item from a receipt."""

    raw_name: str = Field(description="Full item name from receipt, can be multi-line")
    quantity: float = Field(default=1, gt=0, description="Item quantity")
    unit: str = Field(default="ea", description="Unit of measurement (ea, kg, g, L, ml, etc.)")
    price: float = Field(gt=0, description="Item price as shown on receipt (final price after any discount)")
    discount: float = Field(default=0.0, description="Discount amount from separate discount column (0 if no discount)")
    sku: Optional[str] = Field(default=None, description="Product SKU/barcode if visible")
    category: str = Field(default="Other", description="Product category (Produce, Meat, Dairy, Bakery, Pantry, Frozen, Beverage, Household, Other)")
    language: Optional[str] = Field(default="en", description="Detected language of item name")

    # AI guessing fields
    guessed_name: Optional[str] = None
    confidence: Optional[float] = None
    confirmed_name: Optional[str] = None
    needs_review: bool = False

    @property
    def total(self) -> float:
        """Calculate total price for this item."""
        return self.price * self.quantity


class Receipt(BaseModel):
    """Complete receipt data."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    store: str
    datetime: datetime
    processed_at: datetime = Field(default_factory=datetime.now)
    verified: bool = False
    raw_ocr_text: str
    items: list[ReceiptItem]
    total: float
    subtotal: Optional[float] = Field(default=None, description="Subtotal before tax")
    tax: Optional[float] = Field(default=None, description="Tax amount (GST, VAT, sales tax)")
    discount_total: Optional[float] = Field(default=None, description="Total discount amount across all items")
    payment_method: Optional[str] = Field(default=None, description="Payment method (Card, Cash, EFT, etc.)")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class GuessResult(BaseModel):
    """Result from item name guessing."""

    product_name: str
    confidence: float
