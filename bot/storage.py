"""JSON file storage for receipts and guesses."""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from bot.config import settings


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def _get_file_path(filename: str) -> Path:
    """Get the full path for a data file."""
    return settings.data_dir / filename


def calculate_accuracy(guessed: float, actual: float) -> float:
    """
    Calculate accuracy percentage between guessed and actual amounts.
    
    Args:
        guessed: The guessed amount
        actual: The actual amount
    
    Returns:
        Accuracy percentage, clamped between -100 and 100
    """
    if actual == 0:
        return 0.0 if guessed == 0 else -100.0
    
    accuracy = 100 - abs((guessed - actual) / actual * 100)
    return max(-100.0, min(100.0, accuracy))


def load_receipts() -> List[Dict[str, Any]]:
    """Load all receipts from JSON file."""
    file_path = _get_file_path("receipts.json")
    if not file_path.exists():
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_receipts(receipts: List[Dict[str, Any]]) -> None:
    """Save receipts to JSON file."""
    file_path = _get_file_path("receipts.json")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(receipts, f, indent=2, cls=JSONEncoder)
    except IOError as e:
        raise IOError(f"Failed to save receipts: {str(e)}")


def load_guesses() -> List[Dict[str, Any]]:
    """Load all guesses from JSON file."""
    file_path = _get_file_path("guesses.json")
    if not file_path.exists():
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_guesses(guesses: List[Dict[str, Any]]) -> None:
    """Save guesses to JSON file."""
    file_path = _get_file_path("guesses.json")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(guesses, f, indent=2, cls=JSONEncoder)
    except IOError as e:
        raise IOError(f"Failed to save guesses: {str(e)}")


def get_receipt_by_id(receipt_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific receipt by ID."""
    receipts = load_receipts()
    for receipt in receipts:
        if receipt.get('id') == receipt_id:
            return receipt
    return None


def add_receipt(receipt_data: Dict[str, Any]) -> None:
    """Add a new receipt."""
    receipts = load_receipts()
    receipts.append(receipt_data)
    save_receipts(receipts)


def add_guess(guess_data: Dict[str, Any]) -> None:
    """Add a new guess."""
    guesses = load_guesses()
    guesses.append(guess_data)
    save_guesses(guesses)

