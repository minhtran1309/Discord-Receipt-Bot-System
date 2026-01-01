"""OpenRouter API integration for item name guessing."""

import httpx
import json
from bot.models import GuessResult


class ItemGuesser:
    """Service for guessing full product names from abbreviated receipt text."""

    def __init__(self, api_key: str, model: str, corrections: dict[str, str] = None):
        """Initialize item guesser service."""
        self.api_key = api_key
        self.model = model
        self.corrections = corrections or {}
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.client = httpx.AsyncClient(timeout=60.0)

    def update_corrections(self, corrections: dict[str, str]) -> None:
        """Update the corrections dictionary."""
        self.corrections = corrections

    async def guess(self, raw_name: str, store: str) -> GuessResult:
        """Guess the full product name for a receipt item."""
        # Check corrections first
        key = f"{raw_name}|{store}"
        if key in self.corrections:
            return GuessResult(
                product_name=self.corrections[key],
                confidence=1.0,
            )

        # Call AI to guess
        prompt = f"""You are a grocery item identifier. Given an abbreviated item name from a store receipt, guess the full product name.

Store: {store}
Abbreviated name: {raw_name}

Respond in JSON format only:
{{"product_name": "Full Product Name", "confidence": 0.85}}"""

        try:
            response = await self.client.post(
                self.endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            result = response.json()

            # Extract response text
            content = result["choices"][0]["message"]["content"]

            # Parse JSON response
            parsed = json.loads(content)
            return GuessResult(**parsed)

        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            # Return raw name with low confidence if API fails
            return GuessResult(
                product_name=raw_name,
                confidence=0.0,
            )

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
