"""Mistral OCR service using official mistralai package."""

import base64
from typing import Optional, List
from pydantic import BaseModel, Field
from mistralai import Mistral


class OCRReceiptItem(BaseModel):
    """Schema for OCR to extract individual receipt items."""

    raw_name: str = Field(description="Complete item name including all text across multiple lines if applicable")
    quantity: float = Field(default=1.0, description="Quantity purchased")
    unit: str = Field(default="ea", description="Unit type: ea (each), kg, g, L, ml, lb, oz, etc.")
    price: float = Field(description="Item price as shown on receipt (the final price after any discount)")
    discount: float = Field(default=0.0, description="Discount amount if shown in separate discount column (0 if no discount)")
    sku: Optional[str] = Field(default=None, description="Product SKU or barcode number if visible")


class OCRReceiptData(BaseModel):
    """Schema for complete receipt extraction."""

    store_name: str = Field(description="Store name from receipt header")
    store_location: Optional[str] = Field(default=None, description="Store branch or address")
    date: str = Field(description="Transaction date in YYYY-MM-DD format")
    time: Optional[str] = Field(default=None, description="Transaction time in HH:MM format")
    items: List[OCRReceiptItem] = Field(description="List of purchased items with prices")
    subtotal: Optional[float] = Field(default=None, description="Subtotal before tax")
    tax: Optional[float] = Field(default=None, description="Tax amount (GST, VAT, sales tax)")
    discount_total: Optional[float] = Field(default=None, description="Total discount amount")
    total: float = Field(description="Final total amount")
    payment_method: Optional[str] = Field(default=None, description="Payment method used")


class OCRService:
    """Service for processing receipt images with Mistral OCR API."""

    def __init__(self, api_key: str, model: str = "mistral-ocr-latest"):
        """
        Initialize OCR service with Mistral AI client.

        Args:
            api_key: Mistral API key
            model: OCR model to use (default: mistral-ocr-latest)
        """
        self.api_key = api_key
        self.model = model
        self.client = Mistral(api_key=api_key)

    async def process_image(self, image_bytes: bytes, use_structured_extraction: bool = True) -> tuple[str, Optional[OCRReceiptData]]:
        """
        Process receipt image with optional structured extraction.

        Args:
            image_bytes: Raw image bytes
            use_structured_extraction: Whether to use Pydantic schema extraction (default: True)

        Returns:
            tuple: (raw_markdown_text, structured_data or None)
        """
        # Detect MIME type
        mime_type = self._detect_mime_type(image_bytes)

        # Encode image to base64 data URI
        base64_image = base64.standard_b64encode(image_bytes).decode("utf-8")
        image_url = f"data:{mime_type};base64,{base64_image}"

        if use_structured_extraction:
            try:
                # Try structured extraction with Pydantic schema
                from mistralai.extra import response_format_from_pydantic_model

                extraction_schema = response_format_from_pydantic_model(OCRReceiptData)

                response = self.client.ocr.process(
                    model=self.model,
                    document={
                        "type": "image_url",
                        "image_url": image_url,
                    },
                    table_format="html",  # Preserve table structure
                    extract_header=True,
                    extract_footer=False,
                    document_annotation_format=extraction_schema
                )

                # Extract both raw markdown and structured data
                raw_text = response.pages[0].markdown if response.pages else ""
                structured_data = None

                # Parse structured data from annotations
                if hasattr(response, 'annotations') and response.annotations:
                    import json
                    annotation_data = response.annotations[0]
                    structured_data = OCRReceiptData(**json.loads(annotation_data))

                return raw_text, structured_data

            except Exception as e:
                # Fallback to basic extraction if structured fails
                print(f"Structured extraction failed: {e}, falling back to basic OCR")
                use_structured_extraction = False

        # Basic extraction without structure
        try:
            response = self.client.ocr.process(
                model=self.model,
                document={
                    "type": "image_url",
                    "image_url": image_url,
                }
            )

            # Extract markdown text from pages
            if response.pages:
                ocr_text = response.pages[0].markdown
                return ocr_text, None
            else:
                raise Exception("No pages returned from OCR")

        except Exception as e:
            raise Exception(f"OCR API error: {e}") from e

    def _detect_mime_type(self, image_bytes: bytes) -> str:
        """
        Detect MIME type from image bytes.

        Args:
            image_bytes: Raw image bytes

        Returns:
            MIME type string
        """
        if image_bytes.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif image_bytes.startswith(b'\x89PNG'):
            return 'image/png'
        elif image_bytes[:4] == b'ftyp' or image_bytes[4:12] == b'ftypheic':
            return 'image/heic'
        else:
            return 'image/jpeg'  # Default fallback

    async def close(self) -> None:
        """Close the Mistral client."""
        # Mistral SDK may not need explicit close
        # Keep for compatibility with existing code
        pass
