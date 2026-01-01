"""Pydantic data models for the bot."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ReceiptItem(BaseModel):
    """Single item from a receipt."""

    raw_name: str
    quantity: float = Field(default=1, gt=0)
    unit: str = "ea"
    price: float = Field(gt=0)
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

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class GuessResult(BaseModel):
    """Result from item name guessing."""

    product_name: str
    confidence: float
