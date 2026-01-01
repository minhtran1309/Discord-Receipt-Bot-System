"""Tests for storage module."""

import pytest
from datetime import datetime
from bot.storage import Storage
from bot.models import Receipt, ReceiptItem


def test_save_and_load_receipt(tmp_path):
    """Test saving and loading a receipt."""
    storage = Storage(str(tmp_path))

    receipt = Receipt(
        filename="",
        store="Test Store",
        datetime=datetime.now(),
        raw_ocr_text="test text",
        items=[
            ReceiptItem(raw_name="Item 1", price=5.99),
            ReceiptItem(raw_name="Item 2", price=3.49),
        ],
        total=9.48,
    )

    filename = storage.save_receipt(receipt)
    loaded = storage.load_receipt(filename)

    assert loaded is not None
    assert loaded.store == "Test Store"
    assert len(loaded.items) == 2
    assert loaded.total == 9.48


def test_corrections(tmp_path):
    """Test correction storage."""
    storage = Storage(str(tmp_path))

    storage.save_correction("GV MLK", "Walmart", "Great Value Milk")
    corrections = storage.load_corrections()

    assert "GV MLK|Walmart" in corrections
    assert corrections["GV MLK|Walmart"] == "Great Value Milk"

    success = storage.delete_correction("GV MLK", "Walmart")
    assert success is True

    corrections = storage.load_corrections()
    assert "GV MLK|Walmart" not in corrections
