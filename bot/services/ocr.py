"""Mistral OCR service using official mistralai package."""

import base64
from mistralai import Mistral


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

    async def process_image(self, image_bytes: bytes) -> str:
        """
        Process receipt image and return OCR text.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Extracted text from the image as markdown
        """
        # Encode image to base64 data URI
        base64_image = base64.standard_b64encode(image_bytes).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{base64_image}"

        try:
            # Call Mistral OCR API (synchronous client)
            response = self.client.ocr.process(
                model=self.model,
                document={
                    "type": "image_url",
                    "image_url": image_url,
                }
            )

            # Extract markdown text from pages
            if response.pages:
                # Get text from first page (receipts are typically single page)
                ocr_text = response.pages[0].markdown
                return ocr_text
            else:
                raise Exception("No pages returned from OCR")

        except Exception as e:
            raise Exception(f"OCR API error: {e}") from e

    async def close(self) -> None:
        """Close the Mistral client."""
        # Mistral SDK may not need explicit close
        # Keep for compatibility with existing code
        pass
