"""AI-powered receipt data extraction using OpenRouter."""

import json
from datetime import datetime
from typing import Any, Dict

import httpx

from bot.models import Receipt, ReceiptItem


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

    def _detect_major_store(self, ocr_text: str) -> tuple[str | None, bool]:
        """
        Detect if receipt is from Woolworths or Coles.

        Args:
            ocr_text: Raw OCR text

        Returns:
            Tuple of (store_name or None, is_major_store_detected)
        """
        ocr_lower = ocr_text.lower()

        # Woolworths detection
        woolworths_indicators = [
            "woolworths",
            "woolies",
            "www.woolworths.com.au",
            "top ryde",  # Known Woolworths location
            "ryde",
            "auburn",
        ]

        for indicator in woolworths_indicators:
            if indicator in ocr_lower:
                return ("Woolworths", True)

        # Coles detection
        coles_indicators = [
            "coles",
            "www.coles.com.au",
        ]

        for indicator in coles_indicators:
            if indicator in ocr_lower:
                return ("Coles", True)

        return (None, False)

    async def extract_receipt_data(self, ocr_text: str) -> Dict[str, Any]:
        """
        Extract structured data from OCR text using AI.

        Args:
            ocr_text: Raw OCR markdown text

        Returns:
            Extracted receipt data as dict with metadata about major store detection
        """
        # Detect major stores (Woolworths/Coles)
        detected_store, is_major_store = self._detect_major_store(ocr_text)

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
                    "response_format": {"type": "json_object"},
                },
            )

            if response.status_code != 200:
                raise Exception(
                    f"AI extraction failed: {response.status_code} - {response.text}"
                )

            result = response.json()
            extracted_json = result["choices"][0]["message"]["content"]
            extracted_data = json.loads(extracted_json)

            # Override store name if we detected Woolworths/Coles
            if is_major_store and detected_store:
                extracted_data["store_name"] = detected_store
                extracted_data["_major_store_detected"] = True  # Metadata flag
            else:
                extracted_data["_major_store_detected"] = False

            return extracted_data

    def _build_extraction_prompt(self, ocr_text: str) -> str:
        """Build extraction prompt for AI."""
        return f"""You are a receipt data extractor. Analyze this OCR text from a grocery receipt and extract structured data.

OCR Text:
{ocr_text}

Extract the following information in JSON format:
- store_name: Store name from header (normalize "TOP RYDE", "Top Ryde" to "Woolworths", detect "Coles" variants)
  **CRITICAL**: Store name is used for file naming. Extract accurately.
- store_location: Store branch or address (if visible)
- date: Transaction date in YYYY-MM-DD format
  **CRITICAL**: Date is used for file naming. Extract accurately.
- time: Transaction time in HH:MM format (if visible)
- items: Array of items, each with:
  - raw_name: Full item name (combine multi-line names)
  - quantity: Quantity purchased (default 1.0)
  - unit: Unit type (ea, kg, g, L, ml, etc., default "ea")
  - price: Item price as shown (final price after discount, 0.0 for free promotional items)
  - discount: Discount amount from separate column (0 if none)
  - sku: Product SKU/barcode if visible
  - category: Product category (e.g., "Produce", "Meat", "Dairy", "Bakery", "Pantry", "Frozen", "Beverage", "Household", "Other")
- subtotal: Subtotal before tax (if shown)
- tax: Tax amount (GST, VAT, sales tax)
- discount_total: Total discount amount (if shown)
- total: Final total amount (MOST IMPORTANT - must match receipt exactly)
- payment_method: Payment method used (if visible)

CRITICAL RULES:
1. **TOTAL PRICE IS SACRED**: The total field MUST exactly match the receipt's TOTAL line. This is the most important value.
2. **STORE NAME & DATE ARE CRITICAL**: These are used for file naming. Extract with 100% accuracy.
3. **Discount Lines (D/C)**: Lines starting with "D/C - " are NOT separate items. Skip them entirely - they represent discounts already applied to item prices.
4. **Individual item prices**: Do your best but understand they may have rounding differences or hidden adjustments. The TOTAL is what matters most.
5. **Store Detection**:
   - If you see "Woolworths" anywhere OR location names like "Top Ryde", "Ryde", "Auburn", store_name should be "Woolworths"
   - If you see "Coles" anywhere, store_name should be "Coles"
6. **Multi-line items**: Combine items spanning multiple lines into a single raw_name
7. **Units**: Extract units (kg, g, L, ml) separately from item names
8. **Language preservation**: Keep original language for item names (Korean, Chinese, etc.)
9. **Free items**: For free promotional items, set price to 0.0 but include in items array

Return ONLY valid JSON, no markdown formatting."""

    def convert_to_receipt(
        self, extracted_data: Dict[str, Any], raw_ocr_text: str
    ) -> Receipt:
        """
        Convert extracted data to Receipt model.

        Args:
            extracted_data: Extracted data from AI
            raw_ocr_text: Original OCR text

        Returns:
            Receipt object with major_store_detected metadata
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
                category=item.get("category", "Other"),
            )
            for item in extracted_data.get("items", [])
        ]

        # Adjust confidence and mark for review for free items
        for item in items:
            if item.price == 0.0:
                item.confidence = 0.5  # Lower confidence for free items
                item.needs_review = True  # Flag for user verification
                item.guessed_name = item.raw_name  # Use raw name as guess

        # Parse datetime
        try:
            date_str = extracted_data.get("date", "")
            time_str = extracted_data.get("time", "00:00")
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except:
            dt = datetime.now()

        # Helper to convert empty strings to None for optional float fields
        def parse_optional_float(value):
            """Convert empty strings or None to None, otherwise return float value."""
            if value is None or value == "" or value == "N/A":
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        receipt = Receipt(
            filename="",
            store=extracted_data.get("store_name", "Unknown Store"),
            datetime=dt,
            raw_ocr_text=raw_ocr_text,
            items=items,
            total=float(extracted_data.get("total", 0.0)),
            subtotal=parse_optional_float(extracted_data.get("subtotal")),
            tax=parse_optional_float(extracted_data.get("tax")),
            discount_total=parse_optional_float(extracted_data.get("discount_total")),
            payment_method=extracted_data.get("payment_method") or None,
            verified=False,
        )

        # Store major store detection metadata (not persisted)
        receipt._major_store_detected = extracted_data.get("_major_store_detected", False)

        return receipt
