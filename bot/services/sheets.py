"""Google Sheets API integration."""

from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from bot.models import Receipt


class SheetsService:
    """Service for syncing receipt data to Google Sheets."""

    def __init__(self, credentials_path: str, spreadsheet_id: str, bot_name: str = "Receipt Bot (Unknown)"):
        """Initialize Google Sheets service.

        Args:
            credentials_path: Path to Google service account credentials JSON
            spreadsheet_id: Google Sheets spreadsheet ID
            bot_name: Name/identifier of bot instance for tracking (e.g., "Receipt Bot (Dev)")
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.bot_name = bot_name
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

    def get_worksheet(self, worksheet_name: str):
        """Get a specific worksheet by name.

        Args:
            worksheet_name: Name of the worksheet/tab

        Returns:
            Worksheet object
        """
        if not self.client:
            self.connect()

        spreadsheet = self.client.open_by_key(self.spreadsheet_id)

        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            print(f"[Sheets] Accessed worksheet: {worksheet_name}")
            return worksheet
        except gspread.WorksheetNotFound:
            print(f"[Sheets] Worksheet '{worksheet_name}' not found")
            raise

    def append_row(self, worksheet_name: str, row: list):
        """Append a single row to a worksheet.

        Args:
            worksheet_name: Name of worksheet/tab
            row: List of values for the row
        """
        worksheet = self.get_worksheet(worksheet_name)
        worksheet.append_row(row)
        print(f"[Sheets] Appended row to {worksheet_name}")

    def get_all_records(self, worksheet_name: str) -> list[dict]:
        """Get all records from a worksheet as list of dicts.

        Args:
            worksheet_name: Name of worksheet/tab

        Returns:
            List of dicts with column headers as keys
        """
        worksheet = self.get_worksheet(worksheet_name)
        return worksheet.get_all_records()

    def get_cell_value(self, worksheet_name: str, row: int, col: int):
        """Get value from specific cell.

        Args:
            worksheet_name: Name of worksheet/tab
            row: Row number (1-indexed)
            col: Column number (1-indexed)

        Returns:
            Cell value
        """
        worksheet = self.get_worksheet(worksheet_name)
        return worksheet.cell(row, col).value

    def update_cell(self, worksheet_name: str, row: int, col: int, value):
        """Update a specific cell.

        Args:
            worksheet_name: Name of worksheet/tab
            row: Row number (1-indexed)
            col: Column number (1-indexed)
            value: New cell value
        """
        worksheet = self.get_worksheet(worksheet_name)
        worksheet.update_cell(row, col, value)
        print(f"[Sheets] Updated cell ({row},{col}) in {worksheet_name}")

    def parse_formula(self, formula: str) -> list[str]:
        """Extract cell references from an additive formula.

        Args:
            formula: Excel formula (e.g., "=receipt_total!D2+receipt_total!D3")

        Returns:
            List of cell references

        Examples:
            "=receipt_total!D2+receipt_total!D3" -> ["receipt_total!D2", "receipt_total!D3"]
            "=A1" -> ["A1"]
            "" -> []
        """
        if not formula or not formula.startswith("="):
            return []

        # Remove leading "=" and split by "+"
        formula_body = formula[1:]  # Remove "="
        cell_refs = [ref.strip() for ref in formula_body.split("+")]

        return [ref for ref in cell_refs if ref]  # Filter empty strings

    def append_to_formula(self, existing_formula: str, new_cell_ref: str) -> str:
        """Append a cell reference to an existing formula.

        Args:
            existing_formula: Current formula (e.g., "=A1+A2")
            new_cell_ref: Cell reference to append (e.g., "A5")

        Returns:
            Updated formula (e.g., "=A1+A2+A5")
        """
        if not existing_formula or existing_formula.strip() == "":
            # No existing formula, create new one
            return f"={new_cell_ref}"

        # Append to existing formula
        return f"{existing_formula}+{new_cell_ref}"

    def build_formula(self, cell_refs: list[str]) -> str:
        """Build an additive formula from cell references.

        Args:
            cell_refs: List of cell references (e.g., ["A1", "A2", "A5"])

        Returns:
            Formula string (e.g., "=A1+A2+A5")
        """
        if not cell_refs:
            return ""

        return "=" + "+".join(cell_refs)

    def find_or_create_category_row(self, worksheet_name: str, category: str) -> int:
        """Find the row number for a specific category in total_cost_monthly sheet, or create it.

        Args:
            worksheet_name: Name of worksheet (should be "total_cost_monthly")
            category: Category name (shopping_expenses, special_treat, personal, utilities, extraordinary, transport)

        Returns:
            Row number (1-indexed) where the category data is located
        """
        worksheet = self.get_worksheet(worksheet_name)

        # Get all values in first column (Category column)
        all_values = worksheet.col_values(1)

        # Check if category exists
        for idx, value in enumerate(all_values[1:], start=2):  # Skip header row
            if value == category:
                return idx

        # Category not found, append new row
        # Structure: [Category, 2026-01, 2026-02, ...]  (month columns will be created dynamically)
        new_row = [category]  # Just category name, month columns added later
        worksheet.append_row(new_row)

        return len(all_values) + 1  # Return the row number of newly added row

    def find_or_create_month_column(self, worksheet_name: str, month: str) -> int:
        """Find the column number for a specific month in total_cost_monthly sheet, or create it.

        Args:
            worksheet_name: Name of worksheet (should be "total_cost_monthly")
            month: Month in YYYY-MM format (e.g., "2026-01")

        Returns:
            Column number (1-indexed) where the month data is located
        """
        worksheet = self.get_worksheet(worksheet_name)

        # Get all values in first row (Month header row)
        header_row = worksheet.row_values(1)

        # Check if month column exists
        for idx, value in enumerate(header_row[1:], start=2):  # Skip Category column
            if value == month:
                return idx

        # Month not found, add as new column
        # Insert month in header row
        next_col = len(header_row) + 1
        worksheet.update_cell(1, next_col, month)

        return next_col

    def update_formula_cell(self, worksheet_name: str, category: str, month: str, new_cell_ref: str):
        """Update a formula cell in total_cost_monthly sheet by appending a new cell reference.

        Args:
            worksheet_name: Name of worksheet (should be "total_cost_monthly")
            category: Category name (shopping_expenses, special_treat, personal, utilities, extraordinary, transport)
            month: Month in YYYY-MM format
            new_cell_ref: Cell reference to append (e.g., "receipt_total!B5")
        """
        worksheet = self.get_worksheet(worksheet_name)

        # Find or create category row
        category_row = self.find_or_create_category_row(worksheet_name, category)

        # Find or create month column
        month_col = self.find_or_create_month_column(worksheet_name, month)

        # Get existing formula
        existing_formula = worksheet.cell(category_row, month_col).value or ""

        # Append new cell reference
        updated_formula = self.append_to_formula(existing_formula, new_cell_ref)

        # Update cell
        worksheet.update_cell(category_row, month_col, updated_formula)
        print(f"[Sheets] Updated {category} formula for {month}: {updated_formula}")

    def rebuild_formula_from_sheet(self, source_sheet: str, category: str, month: str, amount_column: str = "C") -> str:
        """Read all rows from a source sheet for a specific month and rebuild formula from scratch.

        This method reads from Google Sheets (source of truth) instead of relying on internal memory.

        Args:
            source_sheet: Source sheet name (e.g., "receipt_total", "personal", "utilities")
            category: Category in total_cost_monthly (e.g., "shopping_expenses", "personal")
            month: Month in YYYY-MM format
            amount_column: Column letter where amounts are stored (default "C", "B" for receipt_total)

        Returns:
            Complete formula string (e.g., "=receipt_total!B2+B5+B8")
        """
        worksheet = self.get_worksheet(source_sheet)

        # Get all records
        all_records = worksheet.get_all_values()

        if not all_records or len(all_records) < 2:
            return ""  # No data (only header or empty)

        # Determine month column index based on sheet structure
        header = all_records[0]

        # For receipt_total: check if row matches month (extract from filename or date)
        # For expense sheets: check Month column (column E typically)
        cell_refs = []

        if source_sheet == "receipt_total":
            # For receipt_total, we need to parse filename to determine month
            # Format: YYYY-MM-DD_HHMM_store
            # Column A: receipt_file_name, Column B: total_price
            for row_idx, row in enumerate(all_records[1:], start=2):  # Skip header
                if len(row) < 2:
                    continue

                filename = row[0]  # receipt_file_name
                # Extract date from filename (YYYY-MM-DD_...)
                if filename and "_" in filename:
                    date_part = filename.split("_")[0]  # Get YYYY-MM-DD
                    if date_part and len(date_part) >= 7:
                        row_month = date_part[:7]  # Extract YYYY-MM
                        if row_month == month:
                            cell_refs.append(f"{source_sheet}!B{row_idx}")  # Column B is total_price

        else:
            # For expense sheets (personal, utilities, transport, extraordinary)
            # Structure: [Date, Time, Amount, Category, Month, submitted_by]
            # Month is in column E (index 4)
            month_col_idx = 4

            for row_idx, row in enumerate(all_records[1:], start=2):  # Skip header
                if len(row) <= month_col_idx:
                    continue

                row_month = row[month_col_idx]  # Month column
                if row_month == month:
                    cell_refs.append(f"{source_sheet}!{amount_column}{row_idx}")

        return self.build_formula(cell_refs)

    def sync_receipt(self, receipt: Receipt) -> bool:
        """Sync a single receipt to Google Sheets.

        Returns:
            True if successful, False otherwise
        """
        if not self.worksheet:
            self.connect()

        print(
            f"[Sheets] Syncing receipt: {receipt.filename} ({len(receipt.items)} items)"
        )

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
                self.bot_name,  # Signature column - tracks which bot synced this data
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

    def sync_receipt_totals(self, receipts: list[Receipt], bot_signature: str = "Receipt Bot") -> dict[str, list[str]]:
        """Sync receipt totals to receipt_total sheet and return cell references by month.

        Args:
            receipts: List of Receipt objects to sync
            bot_signature: Bot instance identifier (e.g., "Receipt Bot (Local)")

        Returns:
            Dict mapping month to list of cell references
            Example: {"2026-01": ["receipt_total!B2", "receipt_total!B5"], "2026-02": ["receipt_total!B8"]}
        """
        if not receipts:
            return {}

        worksheet = self.get_worksheet("receipt_total")

        # Get current row count (to determine where to append)
        all_values = worksheet.get_all_values()
        next_row = len(all_values) + 1

        month_cell_refs = {}

        for receipt in receipts:
            if not receipt.verified:
                continue

            month = receipt.datetime.strftime("%Y-%m")

            # Prepare row: [receipt_file_name, total_price, submitted_by, sync_status]
            row = [
                receipt.filename,      # receipt_file_name (column A)
                receipt.total,         # total_price (column B) ← THIS is what formulas reference
                bot_signature,         # submitted_by (column C)
                "synced",             # sync_status (column D)
            ]

            # Append row
            worksheet.append_row(row)
            print(f"[Sheets] Added receipt total to row {next_row}: {receipt.filename} (${receipt.total:.2f})")

            # Track cell reference (total_price is in column B)
            cell_ref = f"receipt_total!B{next_row}"

            if month not in month_cell_refs:
                month_cell_refs[month] = []
            month_cell_refs[month].append(cell_ref)

            next_row += 1

        return month_cell_refs

    def update_shopping_expenses_formulas(self, month_cell_refs: dict[str, list[str]]):
        """Update shopping_expenses formulas in total_cost_monthly sheet.

        Args:
            month_cell_refs: Dict mapping month to list of cell references
        """
        for month, cell_refs in month_cell_refs.items():
            for cell_ref in cell_refs:
                self.update_formula_cell("total_cost_monthly", "shopping_expenses", month, cell_ref)

    def rebuild_all_formulas(self) -> dict[str, int]:
        """Rebuild all formulas in total_cost_monthly by reading from all expense sheets.

        Reads data from:
        - receipt_total → Shopping_expenses
        - extraordinaries → Extraordinary
        - eat_out → Special_treats
        - utilities → Utilities
        - personal → Personal
        - transport → Transport

        Returns:
            Dict with category names as keys and formula count as values
        """
        # Sheet-to-category mapping (sheet_name -> (row_name, amount_column))
        sheet_mappings = {
            "receipt_total": ("Shopping_expenses", "B"),  # (row_name, amount_column)
            "extraordinaries": ("Extraordinary", "C"),
            "eat_out": ("Special_treats", "C"),
            "utilities": ("Utilities", "C"),
            "personal": ("Personal", "C"),
            "transport": ("Transport", "C"),
        }

        # Month name mapping (month_number -> column_name)
        month_names = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
            5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
            9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }

        stats = {}

        for sheet_name, (category_name, amount_col) in sheet_mappings.items():
            try:
                worksheet = self.get_worksheet(sheet_name)
                all_records = worksheet.get_all_values()

                if not all_records or len(all_records) < 2:
                    print(f"[RebuildFormulas] {sheet_name}: No data, skipping")
                    stats[category_name] = 0
                    continue

                # Group rows by month name (Jan, Feb, Mar, etc.)
                months_data = {}  # month_name -> list of row indices

                if sheet_name == "receipt_total":
                    # Extract month from filename (YYYY-MM-DD_HHMM_store)
                    for row_idx, row in enumerate(all_records[1:], start=2):
                        if len(row) < 2:
                            continue
                        filename = row[0]
                        if filename and "_" in filename:
                            date_part = filename.split("_")[0]
                            if date_part and len(date_part) >= 7:
                                # Extract month number from YYYY-MM format
                                month_num = int(date_part[5:7])  # Extract MM
                                month_name = month_names.get(month_num)
                                if month_name:
                                    if month_name not in months_data:
                                        months_data[month_name] = []
                                    months_data[month_name].append(row_idx)
                else:
                    # Extract month from Month column (index 4 for expense sheets)
                    for row_idx, row in enumerate(all_records[1:], start=2):
                        if len(row) > 4:
                            month_value = row[4]  # Month column
                            if month_value:
                                # Check if it's YYYY-MM format
                                if "-" in month_value and len(month_value) >= 7:
                                    month_num = int(month_value[5:7])
                                    month_name = month_names.get(month_num)
                                elif month_value in month_names.values():
                                    # Already in month name format (Jan, Feb, etc.)
                                    month_name = month_value
                                else:
                                    continue

                                if month_name:
                                    if month_name not in months_data:
                                        months_data[month_name] = []
                                    months_data[month_name].append(row_idx)

                # Build and update formulas for each month
                formula_count = 0
                for month_name, row_indices in months_data.items():
                    # Build formula from row indices
                    cell_refs = [f"{sheet_name}!{amount_col}{idx}" for idx in row_indices]
                    formula = self.build_formula(cell_refs)

                    if formula:
                        # Update cell in total_cost_monthly
                        total_sheet = self.get_worksheet("total_cost_monthly")

                        # Find row by category name
                        category_row = self._find_row_by_name(total_sheet, category_name)
                        if not category_row:
                            print(f"[RebuildFormulas] Warning: Category '{category_name}' not found in total_cost_monthly")
                            continue

                        # Find column by month name
                        month_col = self._find_column_by_name(total_sheet, month_name)
                        if not month_col:
                            print(f"[RebuildFormulas] Warning: Month '{month_name}' not found in total_cost_monthly")
                            continue

                        # Update the cell
                        total_sheet.update_cell(category_row, month_col, formula)
                        formula_count += 1
                        print(f"[RebuildFormulas] {category_name}/{month_name}: {len(row_indices)} entries → Row {category_row}, Col {month_col}")

                stats[category_name] = formula_count

            except Exception as e:
                print(f"[RebuildFormulas] Error processing {sheet_name}: {e}")
                import traceback
                traceback.print_exc()
                stats[category_name] = 0

        return stats

    def _find_row_by_name(self, worksheet, row_name: str) -> int | None:
        """Find row number by matching the first column value.

        Args:
            worksheet: Worksheet object
            row_name: Name to search for in first column

        Returns:
            Row number (1-indexed) or None if not found
        """
        try:
            all_values = worksheet.col_values(1)
            for idx, value in enumerate(all_values, start=1):
                if value == row_name:
                    return idx
            return None
        except Exception as e:
            print(f"[FindRow] Error: {e}")
            return None

    def _find_column_by_name(self, worksheet, col_name: str) -> int | None:
        """Find column number by matching the first row value.

        Args:
            worksheet: Worksheet object
            col_name: Name to search for in first row

        Returns:
            Column number (1-indexed) or None if not found
        """
        try:
            header_row = worksheet.row_values(1)
            for idx, value in enumerate(header_row, start=1):
                if value == col_name:
                    return idx
            return None
        except Exception as e:
            print(f"[FindColumn] Error: {e}")
            return None
