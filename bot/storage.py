"""JSON file storage operations."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from bot.models import Receipt


class Storage:
    """Handles storage and retrieval of receipt data."""

    def __init__(self, data_dir: str = "data"):
        """Initialize storage with data directory."""
        self.data_dir = Path(data_dir)
        self.receipts_dir = self.data_dir / "receipts"
        self.corrections_file = self.data_dir / "corrections.json"

        # Create directories if they don't exist
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
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
