"""Google Sheets API integration."""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from bot.models import Receipt


class SheetsService:
    """Service for syncing receipt data to Google Sheets."""

    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """Initialize Google Sheets service."""
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.worksheet = None

    def connect(self) -> None:
        """Connect to Google Sheets."""
        print(f"[Sheets] Connecting to Google Sheets...")
        print(f"[Sheets] Credentials path: {self.credentials_path}")
        print(f"[Sheets] Spreadsheet ID: {self.spreadsheet_id}")

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_file(
            self.credentials_path, scopes=scopes
        )
        print(f"[Sheets] Credentials loaded successfully")

        self.client = gspread.authorize(credentials)
        print(f"[Sheets] Client authorized")

        spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        print(f"[Sheets] Opened spreadsheet: {spreadsheet.title}")

        self.worksheet = spreadsheet.sheet1
        print(f"[Sheets] Using worksheet: {self.worksheet.title}")

    def sync_receipt(self, receipt: Receipt) -> bool:
        """Sync a single receipt to Google Sheets.

        Returns:
            True if successful, False otherwise
        """
        if not self.worksheet:
            self.connect()

        print(f"[Sheets] Syncing receipt: {receipt.filename} ({len(receipt.items)} items)")

        # Prepare rows for each item
        rows = []
        for item in receipt.items:
            row = [
                receipt.datetime.strftime("%Y-%m-%d"),
                receipt.store,
                item.confirmed_name or item.guessed_name or item.raw_name,
                item.quantity,
                item.unit or "ea",
                item.price,
                item.category or "Other",
                item.sku or "",
            ]
            rows.append(row)

        # Append all rows at once
        if rows:
            try:
                print(f"[Sheets] Appending {len(rows)} rows to worksheet")
                self.worksheet.append_rows(rows)
                print(f"[Sheets] Successfully appended rows")
                return True
            except Exception as e:
                print(f"[Sheets] Error appending rows: {e}")
                return False

        return True  # No rows to append, but not an error

    def sync_multiple(self, receipts: list[Receipt]) -> tuple[int, list[str]]:
        """Sync multiple receipts to Google Sheets.

        Returns:
            Tuple of (success_count, list of successfully synced filenames)
        """
        count = 0
        synced_filenames = []

        for receipt in receipts:
            if receipt.verified and not receipt.synced_to_sheets:
                success = self.sync_receipt(receipt)
                if success:
                    count += 1
                    synced_filenames.append(receipt.filename)

        return count, synced_filenames
