"""Mistral OCR API integration."""

import base64
import httpx
from typing import Optional


class OCRService:
    """Service for processing receipt images with Mistral OCR API."""

    def __init__(self, api_key: str, endpoint: str):
        """Initialize OCR service."""
        self.api_key = api_key
        self.endpoint = endpoint
        self.client = httpx.AsyncClient(timeout=60.0)

    async def process_image(self, image_bytes: bytes) -> str:
        """Process receipt image and return OCR text."""
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        try:
            response = await self.client.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"image": base64_image, "model": "mistral-ocr"},
            )
            response.raise_for_status()
            result = response.json()
            return result.get("text", "")
        except httpx.HTTPError as e:
            raise Exception(f"OCR API error: {e}") from e

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
