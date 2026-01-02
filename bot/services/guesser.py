"""OpenRouter SDK integration for item name guessing."""

from openrouter import OpenRouter
from bot.models import GuessResult, ReceiptItem
from typing import Dict, List
import json


class ItemGuesser:
    """Service for guessing full product names from receipt abbreviations."""

    def __init__(self, api_key: str, model: str, corrections: Dict[str, str] = None):
        """
        Initialize guesser with OpenRouter SDK.

        Args:
            api_key: OpenRouter API key
            model: Model to use (e.g., "openai/gpt-4o-mini")
            corrections: Dictionary of manual corrections {raw_name|store: actual_name}
        """
        self.api_key = api_key
        self.model = model
        self.corrections = corrections or {}
        self.client = OpenRouter(api_key=api_key)

    def update_corrections(self, corrections: Dict[str, str]) -> None:
        """Update the corrections dictionary."""
        self.corrections = corrections

    async def guess_batch(
        self, items: List[ReceiptItem], store: str
    ) -> List[GuessResult]:
        """
        Guess full product names for multiple items at once.

        Args:
            items: List of receipt items to guess
            store: Store name for context

        Returns:
            List of GuessResult objects with product_name and confidence
        """
        results = []
        items_to_guess = []
        items_to_guess_indices = []

        # Check corrections first for each item
        for idx, item in enumerate(items):
            key = f"{item.raw_name}|{store}"
            if key in self.corrections:
                # Use cached correction
                results.append(
                    GuessResult(
                        product_name=self.corrections[key],
                        confidence=1.0
                    )
                )
            else:
                # Need to call API
                items_to_guess.append(item)
                items_to_guess_indices.append(idx)
                # Placeholder result to maintain order
                results.append(None)

        # If all items have corrections, return early
        if not items_to_guess:
            return results

        # Build batch prompt for all items needing guessing
        prompt = self._build_batch_prompt(items_to_guess, store)

        try:
            # Call OpenRouter API with batch request
            response = self.client.chat.send(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a grocery item identifier. Respond only with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}  # Ensure JSON response
            )

            # Parse batch response
            content = response.choices[0].message.content
            guesses = json.loads(content)

            # Extract results for each item and insert at correct positions
            for idx, item in enumerate(items_to_guess):
                item_data = guesses.get(item.raw_name, {})
                guess_result = GuessResult(
                    product_name=item_data.get("product_name", item.raw_name),
                    confidence=item_data.get("confidence", 0.5)
                )
                # Insert at the correct position
                results[items_to_guess_indices[idx]] = guess_result

        except Exception as e:
            # If API fails, return raw names with low confidence
            for idx, item in enumerate(items_to_guess):
                guess_result = GuessResult(
                    product_name=item.raw_name,
                    confidence=0.0
                )
                results[items_to_guess_indices[idx]] = guess_result

        return results

    def _build_batch_prompt(self, items: List[ReceiptItem], store: str) -> str:
        """Build prompt for batch item guessing."""
        items_text = "\n".join([f"- {item.raw_name}" for item in items])

        return f"""Given abbreviated item names from a {store} receipt, guess the full product names.

Items to identify:
{items_text}

Respond with JSON in this exact format:
{{
  "item_abbreviation_1": {{"product_name": "Full Product Name", "confidence": 0.85}},
  "item_abbreviation_2": {{"product_name": "Full Product Name", "confidence": 0.90}}
}}

Use the exact abbreviated names as keys. Confidence should be 0.0 to 1.0."""

    async def close(self) -> None:
        """Close the OpenRouter client."""
        # OpenRouter SDK may not need explicit close
        pass
