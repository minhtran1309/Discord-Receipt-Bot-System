"""Tests for OCR service."""

import pytest
from bot.services.ocr import OCRService


@pytest.mark.asyncio
async def test_ocr_service_initialization():
    """Test OCR service initialization."""
    service = OCRService(
        api_key="test_key",
        endpoint="https://test.endpoint",
    )

    assert service.api_key == "test_key"
    assert service.endpoint == "https://test.endpoint"

    await service.close()
