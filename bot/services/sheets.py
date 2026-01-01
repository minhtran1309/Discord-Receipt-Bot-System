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
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_file(
            self.credentials_path, scopes=scopes
        )
        self.client = gspread.authorize(credentials)
        spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        self.worksheet = spreadsheet.sheet1

    def sync_receipt(self, receipt: Receipt) -> None:
        """Sync a single receipt to Google Sheets."""
        if not self.worksheet:
            self.connect()

        # Prepare rows for each item
        rows = []
        for item in receipt.items:
            row = [
                receipt.datetime.strftime("%Y-%m-%d"),
                receipt.store,
                item.confirmed_name or item.guessed_name or item.raw_name,
                item.quantity,
                item.price,
                "",  # Category (to be filled manually)
            ]
            rows.append(row)

        # Append all rows at once
        if rows:
            self.worksheet.append_rows(rows)

    def sync_multiple(self, receipts: list[Receipt]) -> int:
        """Sync multiple receipts to Google Sheets."""
        count = 0
        for receipt in receipts:
            if receipt.verified:
                self.sync_receipt(receipt)
                count += 1
        return count
