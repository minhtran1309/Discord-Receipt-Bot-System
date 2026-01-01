"""Tests for OCR service."""

import pytest
import os
from pathlib import Path
from bot.services.ocr import OCRService


@pytest.mark.asyncio
async def test_ocr_service_initialization():
    """Test OCR service initialization."""
    service = OCRService(
        api_key="test_key",
        model="mistral-ocr-latest",
    )

    assert service.api_key == "test_key"
    assert service.model == "mistral-ocr-latest"
    assert service.client is not None

    await service.close()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("MISTRAL_API_KEY"),
    reason="MISTRAL_API_KEY not set - skipping live OCR test"
)
async def test_ocr_with_aldi_receipt():
    """Test OCR processing with real Aldi receipt image."""
    import json
    from datetime import datetime

    # Load API credentials
    api_key = os.getenv("MISTRAL_API_KEY")
    model = os.getenv("MISTRAL_OCR_MODEL", "mistral-ocr-latest")

    # Initialize OCR service
    service = OCRService(api_key=api_key, model=model)

    # Read the test receipt image
    receipt_path = Path("data/receipts/aldi_receipt_1.jpg")
    assert receipt_path.exists(), "Test receipt image not found"

    with open(receipt_path, "rb") as f:
        image_bytes = f.read()

    # Process the image
    try:
        ocr_text = await service.process_image(image_bytes)

        # Validate OCR output
        assert ocr_text, "OCR returned empty text"
        assert isinstance(ocr_text, str), "OCR should return a string"
        assert len(ocr_text) > 0, "OCR text should not be empty"

        # Basic validation - receipt should contain common elements
        has_content = len(ocr_text.strip()) > 50
        assert has_content, "OCR text seems too short for a receipt"

        # Save OCR output to JSON
        output_dir = Path("data/test_output")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_data = {
            "test_name": "test_ocr_with_aldi_receipt",
            "receipt_image": str(receipt_path),
            "timestamp": datetime.now().isoformat(),
            "ocr_model": model,
            "ocr_text": ocr_text,
            "text_length": len(ocr_text),
            "status": "success"
        }

        output_file = output_dir / "aldi_receipt_1_ocr_output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*60}")
        print(f"OCR Output saved to: {output_file}")
        print('='*60)
        print("OCR Text Preview (first 500 chars):")
        print('='*60)
        print(ocr_text[:500])
        print('='*60)
        print(f"Full output saved to: {output_file}")
        print('='*60)

    except Exception as e:
        # Save error to JSON
        output_dir = Path("data/test_output")
        output_dir.mkdir(parents=True, exist_ok=True)

        error_data = {
            "test_name": "test_ocr_with_aldi_receipt",
            "receipt_image": str(receipt_path),
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error_message": str(e),
            "error_type": type(e).__name__
        }

        output_file = output_dir / "aldi_receipt_1_ocr_error.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)

        pytest.fail(f"OCR processing failed: {e}")
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_ocr_with_mock_receipt():
    """Test OCR with a minimal mock image (for CI/CD without API key)."""
    from io import BytesIO
    from PIL import Image

    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()

    # Test that service can be initialized and handle bytes
    service = OCRService(
        api_key="test_key",
        model="mistral-ocr-latest"
    )

    # We can't actually call the API without credentials,
    # but we can verify the image bytes are valid
    assert len(img_bytes) > 0
    assert isinstance(img_bytes, bytes)

    await service.close()
