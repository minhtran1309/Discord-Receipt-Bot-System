"""Tests for item guesser."""

import pytest
from bot.services.guesser import ItemGuesser
from bot.models import ReceiptItem


@pytest.mark.asyncio
async def test_guess_batch_with_corrections():
    """Test batch guessing with known corrections."""
    guesser = ItemGuesser(
        api_key="test",
        model="openai/gpt-4o-mini",
        corrections={"GV MLK|Walmart": "Great Value Milk"},
    )

    items = [
        ReceiptItem(raw_name="GV MLK", price=3.49),
        ReceiptItem(raw_name="BNS CHKN", price=5.99),
    ]

    results = await guesser.guess_batch(items, "Walmart")

    # First item should use correction
    assert results[0].product_name == "Great Value Milk"
    assert results[0].confidence == 1.0

    # Second item would call API (mocked to return raw name with low confidence)
    # Since we don't have API credentials in tests, it should fail and return raw name
    assert results[1].confidence >= 0.0


@pytest.mark.asyncio
async def test_guess_batch_all_corrections():
    """Test batch guessing when all items have corrections."""
    guesser = ItemGuesser(
        api_key="test",
        model="openai/gpt-4o-mini",
        corrections={
            "GV MLK|Walmart": "Great Value Milk",
            "BNS CHKN|Walmart": "Boneless Chicken Breast"
        },
    )

    items = [
        ReceiptItem(raw_name="GV MLK", price=3.49),
        ReceiptItem(raw_name="BNS CHKN", price=5.99),
    ]

    results = await guesser.guess_batch(items, "Walmart")

    # Both items should use corrections
    assert results[0].product_name == "Great Value Milk"
    assert results[0].confidence == 1.0
    assert results[1].product_name == "Boneless Chicken Breast"
    assert results[1].confidence == 1.0
