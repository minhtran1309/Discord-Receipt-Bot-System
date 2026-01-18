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

    async def process_image(
        self,
        image_bytes: bytes,
        openrouter_key: str | None = None,
        fallback_model: str = "qwen/qwen3-vl-30b-a3b-instruct",
    ) -> str:
        """
        Process receipt image and return OCR text with fallback.

        Args:
            image_bytes: Raw image bytes
            openrouter_key: Optional OpenRouter API key for fallback
            fallback_model: Vision model to use as fallback

        Returns:
            Extracted markdown text from receipt
        """
        # Detect MIME type
        mime_type = self._detect_mime_type(image_bytes)

        # Encode image to base64 data URI
        base64_image = base64.standard_b64encode(image_bytes).decode("utf-8")
        image_url = f"data:{mime_type};base64,{base64_image}"

        # Try Mistral OCR first
        try:
            response = self.client.ocr.process(
                model=self.model,
                document={
                    "type": "image_url",
                    "image_url": image_url,
                },
            )

            # Extract markdown text from pages
            if response.pages:
                return response.pages[0].markdown
            else:
                raise Exception("No pages returned from OCR")

        except Exception as e:
            error_str = str(e)

            # Check if it's a 429 rate limit error
            if "429" in error_str or "rate" in error_str.lower():
                if openrouter_key:
                    print(
                        f"⚠️ Mistral OCR rate limited (429), falling back to OpenRouter vision model..."
                    )
                    try:
                        return await self.process_image_with_vision(
                            image_bytes, openrouter_key, fallback_model
                        )
                    except Exception as fallback_error:
                        raise Exception(
                            f"Both OCR methods failed. Mistral: {e}, OpenRouter: {fallback_error}"
                        ) from fallback_error
                else:
                    raise Exception(
                        f"Mistral OCR rate limited (429) but no fallback key provided: {e}"
                    ) from e

            # For non-429 errors, raise immediately
            raise Exception(f"OCR API error: {e}") from e

    async def process_image_with_vision(
        self,
        image_bytes: bytes,
        openrouter_key: str,
        model: str = "qwen/qwen3-vl-30b-a3b-instruct",
    ) -> str:
        """
        Fallback OCR using OpenRouter vision model.

        Args:
            image_bytes: Receipt image bytes
            openrouter_key: OpenRouter API key
            model: Vision model to use (default: qwen/qwen3-vl-30b-a3b-instruct)

        Returns:
            Markdown text extracted from image
        """
        import httpx

        # Encode image to base64
        mime_type = self._detect_mime_type(image_bytes)
        base64_image = base64.standard_b64encode(image_bytes).decode("utf-8")
        image_url = f"data:{mime_type};base64,{base64_image}"

        # Call OpenRouter with vision model
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openrouter_key}",
                    "HTTP-Referer": "https://github.com/discord-receipt-bot",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extract all text from this receipt image. Return the text in markdown format, preserving the layout and structure.",
                                },
                                {"type": "image_url", "image_url": {"url": image_url}},
                            ],
                        }
                    ],
                },
            )

            if response.status_code != 200:
                raise Exception(
                    f"Vision OCR API error: {response.status_code} - {response.text}"
                )

            result = response.json()
            return result["choices"][0]["message"]["content"]

    def _detect_mime_type(self, image_bytes: bytes) -> str:
        """
        Detect MIME type from image bytes.

        Args:
            image_bytes: Raw image bytes

        Returns:
            MIME type string
        """
        if image_bytes.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        elif image_bytes.startswith(b"\x89PNG"):
            return "image/png"
        elif image_bytes[:4] == b"ftyp" or image_bytes[4:12] == b"ftypheic":
            return "image/heic"
        else:
            return "image/jpeg"  # Default fallback

    async def close(self) -> None:
        """Close the Mistral client."""
        # Mistral SDK may not need explicit close
        # Keep for compatibility with existing code
        pass
