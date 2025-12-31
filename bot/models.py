"""Pydantic models for receipts and receipt items."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ReceiptItem(BaseModel):
    """Individual item on a receipt."""
    
    name: str
    price: float = Field(gt=0)
    quantity: int = Field(default=1, gt=0)
    
    @property
    def total(self) -> float:
        """Calculate total price for this item."""
        return self.price * self.quantity


class Receipt(BaseModel):
    """Receipt model containing items and metadata."""
    
    id: str
    user_id: int
    username: str
    items: List[ReceiptItem]
    timestamp: datetime = Field(default_factory=datetime.now)
    total_amount: float = Field(default=0.0)
    notes: Optional[str] = None
    
    def calculate_total(self) -> float:
        """Calculate total amount from all items."""
        return sum(item.total for item in self.items)
    
    def model_post_init(self, __context) -> None:
        """Update total amount after initialization."""
        if not self.total_amount:
            self.total_amount = self.calculate_total()
