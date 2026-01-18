"""JSON file storage operations."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from bot.models import Receipt


class Storage:
    """Handles storage and retrieval of receipt data."""

    def __init__(self, data_dir: str = "data"):
        """Initialize storage with data directory."""
        self.data_dir = Path(data_dir)
        self.receipts_dir = self.data_dir / "receipts"
        self.ocr_cache_dir = self.data_dir / "ocr_cache"
        self.corrections_file = self.data_dir / "corrections.json"

        # Create directories if they don't exist
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        self.ocr_cache_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize corrections file
        if not self.corrections_file.exists():
            self._save_json(self.corrections_file, {})

    def _save_json(self, path: Path, data: dict) -> None:
        """Save data to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_json(self, path: Path) -> dict:
        """Load data from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_receipt(self, receipt: Receipt) -> str:
        """Save receipt to file and return filename."""
        # Generate filename: YYYY-MM-DD_HHMM_store.json
        dt = receipt.datetime
        store_name = receipt.store.lower().replace(" ", "_")
        filename = f"{dt.strftime('%Y-%m-%d_%H%M')}_{store_name}.json"
        receipt.filename = filename

        filepath = self.receipts_dir / filename
        receipt_dict = receipt.model_dump(mode="json")
        self._save_json(filepath, receipt_dict)

        return filename

    def load_receipt(self, filename: str) -> Optional[Receipt]:
        """Load receipt from file."""
        filepath = self.receipts_dir / filename
        if not filepath.exists():
            return None

        data = self._load_json(filepath)
        return Receipt(**data)

    def list_receipts(self) -> list[str]:
        """List all receipt filenames."""
        return sorted([f.name for f in self.receipts_dir.glob("*.json")])

    def delete_receipt(self, filename: str) -> bool:
        """Delete a receipt file."""
        filepath = self.receipts_dir / filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def load_corrections(self) -> dict[str, str]:
        """Load item name corrections."""
        return self._load_json(self.corrections_file)

    def save_correction(self, raw_name: str, store: str, actual_name: str) -> None:
        """Save a correction mapping."""
        corrections = self.load_corrections()
        key = f"{raw_name}|{store}"
        corrections[key] = actual_name
        self._save_json(self.corrections_file, corrections)

    def delete_correction(self, raw_name: str, store: str) -> bool:
        """Delete a correction mapping."""
        corrections = self.load_corrections()
        key = f"{raw_name}|{store}"
        if key in corrections:
            del corrections[key]
            self._save_json(self.corrections_file, corrections)
            return True
        return False

    def mark_receipt_synced(self, filename: str) -> bool:
        """Mark a receipt as synced to Google Sheets.

        Args:
            filename: Receipt filename

        Returns:
            True if successful, False otherwise
        """
        receipt = self.load_receipt(filename)
        if not receipt:
            return False

        receipt.synced_to_sheets = True
        self.save_receipt(receipt)
        return True

    def list_unsynced_verified_receipts(self) -> list[Receipt]:
        """Get all verified receipts that haven't been synced to sheets.

        Returns:
            List of verified, unsynced receipts
        """
        filenames = self.list_receipts()
        unsynced = []

        for filename in filenames:
            receipt = self.load_receipt(filename)
            if receipt and receipt.verified and not receipt.synced_to_sheets:
                unsynced.append(receipt)

        return unsynced

    def save_ocr_result(self, filename: str, ocr_text: str) -> None:
        """Save OCR result to cache directory.

        Args:
            filename: Receipt filename (e.g., '2024-01-15_1430_walmart')
            ocr_text: OCR text from API
        """
        cache_file = self.ocr_cache_dir / f"{filename}_ocr.txt"
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(ocr_text)

    def load_ocr_result(self, filename: str) -> Optional[str]:
        """Load OCR result from cache directory.

        Args:
            filename: Receipt filename without extension (e.g., '2024-01-15_1430_walmart')

        Returns:
            OCR text if found, None otherwise
        """
        cache_file = self.ocr_cache_dir / f"{filename}_ocr.txt"

        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def get_latest_ocr_cache(self) -> Optional[tuple[str, str]]:
        """Get the most recently modified OCR cache file.

        Returns:
            Tuple of (filename_without_ext, ocr_text) if found, None otherwise
        """
        cache_files = list(self.ocr_cache_dir.glob("*_ocr.txt"))

        if not cache_files:
            return None

        # Sort by modification time, newest first
        latest_file = max(cache_files, key=lambda f: f.stat().st_mtime)
        filename = latest_file.stem.replace("_ocr", "")

        with open(latest_file, "r", encoding="utf-8") as f:
            ocr_text = f.read()

        return (filename, ocr_text)

    def rename_ocr_cache(self, old_filename: str, new_filename: str) -> bool:
        """Rename an OCR cache file.

        Args:
            old_filename: Old filename without extension (e.g., 'TEMP_1234567890')
            new_filename: New filename without extension (e.g., '2024-01-15_1430_walmart')

        Returns:
            True if successful, False otherwise
        """
        old_cache_file = self.ocr_cache_dir / f"{old_filename}_ocr.txt"
        new_cache_file = self.ocr_cache_dir / f"{new_filename}_ocr.txt"

        if old_cache_file.exists():
            old_cache_file.rename(new_cache_file)
            return True
        return False

    def list_ocr_caches(self) -> list[str]:
        """List all OCR cache filenames (without extensions).

        Returns:
            List of cache filenames sorted by modification time (newest first)
        """
        cache_files = sorted(
            self.ocr_cache_dir.glob("*_ocr.txt"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        return [f.stem.replace("_ocr", "") for f in cache_files]
