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
            Extracted markdown text from receipt
        """
        # Detect MIME type
        mime_type = self._detect_mime_type(image_bytes)

        # Encode image to base64 data URI
        base64_image = base64.standard_b64encode(image_bytes).decode("utf-8")
        image_url = f"data:{mime_type};base64,{base64_image}"

        # Basic OCR extraction
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
                return response.pages[0].markdown
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
