import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from mistralai import Mistral

# Load environment variables
load_dotenv()

# ============================================
# CONFIGURATION - Edit this path
# ============================================
IMAGE_PATH = "../data/receipts/aldi_receipt_1.jpg"  # <-- Change this to your image path
# ====================================
# ========


def encode_image(image_path: str) -> tuple[str, str]:
    """Encode image to base64 and determine MIME type."""
    with open(image_path, "rb") as f:
        base64_data = base64.standard_b64encode(f.read()).decode("utf-8")
    
    ext = Path(image_path).suffix.lower()
    mime_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    mime_type = mime_types.get(ext, "image/jpeg")
    
    return base64_data, mime_type


def main():
    # Check API key
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: Set MISTRAL_API_KEY in .env file")
        return
    
    # Check image exists
    if not os.path.exists(IMAGE_PATH):
        print(f"ERROR: Image not found: {IMAGE_PATH}")
        return
    
    print(f"Processing: {IMAGE_PATH}")
    
    # Initialize client
    client = Mistral(api_key=api_key)
    
    # Encode image
    base64_image, mime_type = encode_image(IMAGE_PATH)
    image_url = f"data:{mime_type};base64,{base64_image}"
    
    # Call OCR API
    print("Calling Mistral OCR API...")
    response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "image_url",
            "image_url": image_url,
        }
    )
    
    # Extract and print result
    if response.pages:
        ocr_text = response.pages[0].markdown
        print("\n" + "=" * 50)
        print("OCR RESULT:")
        print("=" * 50)
        print(ocr_text)
        print("=" * 50)
        
        # Save to file
        output_file = Path(IMAGE_PATH).stem + "_ocr.txt"
        with open(output_file, "w") as f:
            f.write(ocr_text)
        print(f"\nSaved to: {output_file}")
    else:
        print("No text extracted from image")


if __name__ == "__main__":
    main()