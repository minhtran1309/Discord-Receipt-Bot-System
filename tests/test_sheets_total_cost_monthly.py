"""Unit tests for accessing total_cost_monthly sheet and retrieving row/column names."""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

from bot.config import get_settings
from bot.services.sheets import SheetsService


class TestTotalCostMonthlySheet:
    """Test suite for total_cost_monthly sheet access."""

    @pytest.fixture
    def sheets_service(self):
        """Create a SheetsService instance with credentials from settings."""
        settings = get_settings()

        # Verify credentials file exists
        credentials_path = Path(settings.google_credentials_path)
        if not credentials_path.exists():
            pytest.skip(f"Google credentials not found at {credentials_path}")

        service = SheetsService(
            credentials_path=str(credentials_path),
            spreadsheet_id=settings.google_spreadsheet_id,
            bot_name="Test Bot",
        )

        # Connect to Google Sheets
        service.connect()

        return service

    def test_access_total_cost_monthly_sheet(self, sheets_service):
        """Test accessing the total_cost_monthly sheet."""
        try:
            worksheet = sheets_service.get_worksheet("total_cost_monthly")
            assert worksheet is not None
            assert worksheet.title == "total_cost_monthly"
            print(f"✅ Successfully accessed worksheet: {worksheet.title}")
        except Exception as e:
            pytest.fail(f"Failed to access total_cost_monthly sheet: {e}")

    def test_get_row_names(self, sheets_service):
        """Test retrieving all row names (categories) from total_cost_monthly sheet."""
        try:
            worksheet = sheets_service.get_worksheet("total_cost_monthly")

            # Get all values in the first column (Category column)
            all_values = worksheet.col_values(1)

            # First row is the header ("Category")
            header = all_values[0] if all_values else None

            # Remaining rows are category names
            category_names = all_values[1:] if len(all_values) > 1 else []

            print("\n" + "=" * 60)
            print("TOTAL_COST_MONTHLY - ROW NAMES (CATEGORIES)")
            print("=" * 60)
            print(f"Header: {header}")
            print(f"\nCategories (Total: {len(category_names)}):")
            for idx, category in enumerate(category_names, start=1):
                print(f"  Row {idx + 1}: {category}")
            print("=" * 60)

            # Assertions
            assert header == "Category", f"Expected header 'Category', got '{header}'"
            assert (
                len(category_names) > 0
            ), "No categories found in total_cost_monthly sheet"

            # Return for potential use in other tests
            return {
                "header": header,
                "categories": category_names,
                "total_rows": len(category_names) + 1,  # +1 for header
            }

        except Exception as e:
            pytest.fail(f"Failed to retrieve row names: {e}")

    def test_get_column_names(self, sheets_service):
        """Test retrieving all column names (months) from total_cost_monthly sheet."""
        try:
            worksheet = sheets_service.get_worksheet("total_cost_monthly")

            # Get all values in the first row (Month header row)
            header_row = worksheet.row_values(1)

            # First column is "Category"
            category_header = header_row[0] if header_row else None

            # Remaining columns are month names (YYYY-MM format)
            month_columns = header_row[1:] if len(header_row) > 1 else []

            print("\n" + "=" * 60)
            print("TOTAL_COST_MONTHLY - COLUMN NAMES (MONTHS)")
            print("=" * 60)
            print(f"First Column Header: {category_header}")
            print(f"\nMonth Columns (Total: {len(month_columns)}):")
            for idx, month in enumerate(month_columns, start=2):
                col_letter = self._get_column_letter(idx)
                print(f"  Column {col_letter} (#{idx}): {month}")
            print("=" * 60)

            # Assertions
            assert (
                category_header == "Category"
            ), f"Expected first column 'Category', got '{category_header}'"
            assert (
                len(month_columns) > 0
            ), "No month columns found in total_cost_monthly sheet"

            # Validate month format (YYYY-MM)
            for month in month_columns:
                if month:  # Skip empty cells
                    assert (
                        len(month) == 7 and month[4] == "-"
                    ), f"Invalid month format '{month}', expected YYYY-MM"

            # Return for potential use in other tests
            return {
                "category_header": category_header,
                "months": month_columns,
                "total_columns": len(month_columns) + 1,  # +1 for Category column
            }

        except Exception as e:
            pytest.fail(f"Failed to retrieve column names: {e}")

    def test_get_complete_table_structure(self, sheets_service):
        """Test retrieving complete table structure with both rows and columns."""
        try:
            worksheet = sheets_service.get_worksheet("total_cost_monthly")

            # Get all values from the sheet
            all_values = worksheet.get_all_values()

            if not all_values:
                pytest.fail("Sheet is empty")

            # Extract header row (months)
            header_row = all_values[0]
            category_header = header_row[0]
            month_columns = header_row[1:]

            # Extract category column (rows)
            category_rows = (
                [row[0] for row in all_values[1:]] if len(all_values) > 1 else []
            )

            print("\n" + "=" * 80)
            print("TOTAL_COST_MONTHLY - COMPLETE TABLE STRUCTURE")
            print("=" * 80)
            print(
                f"Dimensions: {len(category_rows)} categories × {len(month_columns)} months"
            )
            print(f"\nFirst Column Header: {category_header}")
            print(f"\nCategories (Rows):")
            for idx, category in enumerate(category_rows, start=2):
                print(f"  Row {idx}: {category}")

            print(f"\nMonths (Columns):")
            for idx, month in enumerate(month_columns, start=2):
                col_letter = self._get_column_letter(idx)
                print(f"  Column {col_letter}: {month}")

            print("\nSample Data (First 5 rows × First 3 columns):")
            print("-" * 80)
            for i, row in enumerate(all_values[:5]):
                row_preview = row[:4]  # Category + first 3 months
                print(f"  Row {i+1}: {row_preview}")
            print("=" * 80)

            # Return complete structure
            return {
                "header_row": header_row,
                "category_header": category_header,
                "months": month_columns,
                "categories": category_rows,
                "total_rows": len(all_values),
                "total_columns": len(header_row),
                "all_values": all_values,
            }

        except Exception as e:
            pytest.fail(f"Failed to retrieve complete table structure: {e}")

    def test_find_specific_category(self, sheets_service):
        """Test finding a specific category row in the sheet."""
        try:
            # Test finding Shopping_expenses category
            category_row = sheets_service.find_or_create_category_row(
                "total_cost_monthly", "Shopping_expenses"
            )

            assert (
                category_row >= 2
            ), "Category row should be at least row 2 (after header)"
            print(f"\n✅ Found 'Shopping_expenses' at row {category_row}")

            # Verify the category name
            worksheet = sheets_service.get_worksheet("total_cost_monthly")
            actual_category = worksheet.cell(category_row, 1).value
            assert (
                actual_category == "Shopping_expenses"
            ), f"Expected 'Shopping_expenses', got '{actual_category}'"

        except Exception as e:
            pytest.fail(f"Failed to find specific category: {e}")

    def test_find_specific_month(self, sheets_service):
        """Test finding a specific month column in the sheet."""
        try:
            # Test finding 2026-01 month column
            month_col = sheets_service.find_or_create_month_column(
                "total_cost_monthly", "2026-01"
            )

            assert (
                month_col >= 2
            ), "Month column should be at least column 2 (after Category)"
            col_letter = self._get_column_letter(month_col)
            print(f"\n✅ Found '2026-01' at column {col_letter} (#{month_col})")

            # Verify the month value
            worksheet = sheets_service.get_worksheet("total_cost_monthly")
            actual_month = worksheet.cell(1, month_col).value
            assert (
                actual_month == "2026-01"
            ), f"Expected '2026-01', got '{actual_month}'"

        except Exception as e:
            pytest.fail(f"Failed to find specific month: {e}")

    def test_get_cell_value_by_category_and_month(self, sheets_service):
        """Test retrieving a specific cell value by category and month."""
        try:
            # Find Shopping_expenses row
            category_row = sheets_service.find_or_create_category_row(
                "total_cost_monthly", "Shopping_expenses"
            )

            # Find 2026-01 month column
            month_col = sheets_service.find_or_create_month_column(
                "total_cost_monthly", "2026-01"
            )

            # Get cell value (formula)
            worksheet = sheets_service.get_worksheet("total_cost_monthly")
            cell_value = worksheet.cell(category_row, month_col).value

            col_letter = self._get_column_letter(month_col)
            print(
                f"\n✅ Cell value at Shopping_expenses × 2026-01 (Row {category_row}, Col {col_letter}):"
            )
            print(f"   {cell_value}")

            # If it's a formula, parse it
            if cell_value and cell_value.startswith("="):
                cell_refs = sheets_service.parse_formula(cell_value)
                print(f"\n   Parsed formula contains {len(cell_refs)} cell references:")
                for ref in cell_refs[:5]:  # Show first 5
                    print(f"     - {ref}")
                if len(cell_refs) > 5:
                    print(f"     ... and {len(cell_refs) - 5} more")

            return {
                "category": "Shopping_expenses",
                "month": "2026-01",
                "row": category_row,
                "column": month_col,
                "value": cell_value,
            }

        except Exception as e:
            pytest.fail(f"Failed to retrieve cell value: {e}")

    @staticmethod
    def _get_column_letter(col_num: int) -> str:
        """Convert column number to letter (1 -> A, 27 -> AA, etc.)."""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(65 + (col_num % 26)) + result
            col_num //= 26
        return result


# Standalone test function (can be run directly)
def test_quick_access():
    """Quick test for manual execution - prints all row and column names."""
    try:
        settings = get_settings()

        service = SheetsService(
            credentials_path=settings.google_credentials_path,
            spreadsheet_id=settings.google_spreadsheet_id,
            bot_name="Test Bot",
        )

        service.connect()

        worksheet = service.get_worksheet("total_cost_monthly")

        # Get rows (categories)
        categories = worksheet.col_values(1)

        # Get columns (months)
        months = worksheet.row_values(1)

        print("\n" + "=" * 60)
        print("TOTAL_COST_MONTHLY SHEET - QUICK ACCESS")
        print("=" * 60)
        print(f"\n📊 Row Names (Categories): {len(categories) - 1} total")
        for idx, cat in enumerate(categories):
            print(f"   Row {idx + 1}: {cat}")

        print(f"\n📅 Column Names (Months): {len(months) - 1} total")
        for idx, month in enumerate(months):
            col_letter = TestTotalCostMonthlySheet._get_column_letter(idx + 1)
            print(f"   Column {col_letter}: {month}")

        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run the quick test when executed directly
    test_quick_access()
