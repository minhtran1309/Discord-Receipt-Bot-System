"""AI-powered receipt data extraction using OpenRouter."""

import httpx
import json
from typing import Dict, Any
from bot.models import Receipt, ReceiptItem
from datetime import datetime


class AIExtractor:
    """Extract structured receipt data from OCR text using AI."""

    def __init__(self, api_key: str, model: str = "openai/gpt-4o-mini"):
        """
        Initialize AI extractor with OpenRouter API.

        Args:
            api_key: OpenRouter API key
            model: Model to use for extraction (default: openai/gpt-4o-mini)
        """
        self.api_key = api_key
        self.model = model

    async def extract_receipt_data(self, ocr_text: str) -> Dict[str, Any]:
        """
        Extract structured data from OCR text using AI.

        Args:
            ocr_text: Raw OCR markdown text

        Returns:
            Extracted receipt data as dict matching OCRReceiptData schema
        """
        prompt = self._build_extraction_prompt(ocr_text)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }
            )

            if response.status_code != 200:
                raise Exception(f"AI extraction failed: {response.status_code} - {response.text}")

            result = response.json()
            extracted_json = result["choices"][0]["message"]["content"]
            return json.loads(extracted_json)

    def _build_extraction_prompt(self, ocr_text: str) -> str:
        """Build extraction prompt for AI."""
        return f"""You are a receipt data extractor. Analyze this OCR text from a grocery receipt and extract structured data.

OCR Text:
{ocr_text}

Extract the following information in JSON format:
- store_name: Store name from header
- store_location: Store branch or address (if visible)
- date: Transaction date in YYYY-MM-DD format
- time: Transaction time in HH:MM format (if visible)
- items: Array of items, each with:
  - raw_name: Full item name (combine multi-line names)
  - quantity: Quantity purchased (default 1.0)
  - unit: Unit type (ea, kg, g, L, ml, etc., default "ea")
  - price: Item price as shown (final price after discount)
  - discount: Discount amount from separate column (0 if none)
  - sku: Product SKU/barcode if visible
  - category: Product category (e.g., "Produce", "Meat", "Dairy", "Bakery", "Pantry", "Frozen", "Beverage", "Household", "Other")
- subtotal: Subtotal before tax (if shown)
- tax: Tax amount (GST, VAT, sales tax)
- discount_total: Total discount amount (if shown)
- total: Final total amount
- payment_method: Payment method used (if visible)

Important:
1. For multi-line items, combine them into a single raw_name
2. Extract units (kg, g, L, ml) separately from item names
3. Price should be the final price customer pays
4. Discount is a separate field (0 if no discount column)
5. Preserve original language for item names (Korean, Chinese, etc.)
6. Categorize each item based on the product name

Return ONLY valid JSON, no markdown formatting."""

    def convert_to_receipt(self, extracted_data: Dict[str, Any], raw_ocr_text: str) -> Receipt:
        """
        Convert extracted data to Receipt model.

        Args:
            extracted_data: Extracted data from AI
            raw_ocr_text: Original OCR text

        Returns:
            Receipt object
        """
        # Convert items
        items = [
            ReceiptItem(
                raw_name=item.get("raw_name", ""),
                quantity=item.get("quantity", 1.0),
                unit=item.get("unit", "ea"),
                price=item.get("price", 0.0),
                discount=item.get("discount", 0.0),
                sku=item.get("sku"),
                category=item.get("category", "Other")
            )
            for item in extracted_data.get("items", [])
        ]

        # Parse datetime
        try:
            date_str = extracted_data.get("date", "")
            time_str = extracted_data.get("time", "00:00")
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except:
            dt = datetime.now()

        return Receipt(
            filename="",
            store=extracted_data.get("store_name", "Unknown Store"),
            datetime=dt,
            raw_ocr_text=raw_ocr_text,
            items=items,
            total=extracted_data.get("total", 0.0),
            subtotal=extracted_data.get("subtotal"),
            tax=extracted_data.get("tax"),
            discount_total=extracted_data.get("discount_total"),
            payment_method=extracted_data.get("payment_method"),
            verified=False,
        )
