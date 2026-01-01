"""Tests for item guesser."""

import pytest
from bot.services.guesser import ItemGuesser


@pytest.mark.asyncio
async def test_guess_with_correction():
    """Test guessing with a known correction."""
    guesser = ItemGuesser(
        api_key="test",
        model="test-model",
        corrections={"GV MLK|Walmart": "Great Value Milk"},
    )

    result = await guesser.guess("GV MLK", "Walmart")

    assert result.product_name == "Great Value Milk"
    assert result.confidence == 1.0
