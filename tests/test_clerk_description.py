"""Unit tests for description field in clerk expense commands."""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.cogs.clerk import ClerkCog
from bot.models import BudgetEntry
from bot.services.sheets import SheetsService
from bot.storage import Storage
from bot.budget_storage import BudgetStorage


class TestClerkDescriptionField:
    """Test suite for description field in expense tracking commands."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock Discord bot."""
        bot = Mock()
        bot.settings = Mock()
        bot.settings.bot_name = "Test Bot"
        return bot

    @pytest.fixture
    def mock_sheets_service(self):
        """Create a mock SheetsService."""
        sheets = Mock(spec=SheetsService)

        # Mock append_row method
        sheets.append_row = Mock()

        # Mock get_worksheet to return a mock worksheet with description column
        mock_worksheet = Mock()
        # Correct structure: [Date, Time, Amount, Category, Month, submitted_by, Description]
        mock_worksheet.get_all_values = Mock(
            return_value=[
                [
                    "Date",
                    "Time",
                    "Amount",
                    "Category",
                    "Month",
                    "submitted_by",
                    "Description",
                ],
                [
                    "2026-01-15",
                    "10:30",
                    "50.00",
                    "personal",
                    "2026-01",
                    "Test Bot",
                    "Groceries",
                ],
                [
                    "2026-01-20",
                    "15:45",
                    "75.50",
                    "utilities",
                    "2026-01",
                    "Test Bot",
                    "Internet bill",
                ],
            ]
        )
        sheets.get_worksheet = Mock(return_value=mock_worksheet)

        # Mock rebuild_formula_from_sheet
        sheets.rebuild_formula_from_sheet = Mock(return_value="=personal!C2+personal!C3")

        # Mock find_or_create_category_row and find_or_create_month_column
        sheets.find_or_create_category_row = Mock(return_value=2)
        sheets.find_or_create_month_column = Mock(return_value=3)

        return sheets

    @pytest.fixture
    def mock_storage(self):
        """Create a mock Storage."""
        return Mock(spec=Storage)

    @pytest.fixture
    def mock_budget_storage(self):
        """Create a mock BudgetStorage."""
        budget_storage = Mock(spec=BudgetStorage)

        # Mock save_entry
        budget_storage.save_entry = Mock(return_value="2026-01-15_1030_budget.json")

        # Mock get_monthly_budget
        from bot.models import MonthlyBudget

        mock_budget = MonthlyBudget(
            month="2026-01",
            budget_limit=100.0,
            spent=45.0,
            remaining=55.0,
            entries=[],
            overspent=False,
            surplus=55.0,
        )
        budget_storage.get_monthly_budget = Mock(return_value=mock_budget)

        # Mock get_year_surplus
        budget_storage.get_year_surplus = Mock(return_value=150.0)

        return budget_storage

    @pytest.fixture
    def clerk_cog(self, mock_bot, mock_sheets_service, mock_storage, mock_budget_storage):
        """Create ClerkCog instance with mocked dependencies."""
        cog = ClerkCog(mock_bot, mock_sheets_service, mock_storage)
        cog.budget_storage = mock_budget_storage
        return cog

    @pytest.fixture
    def mock_interaction(self):
        """Create a mock Discord interaction."""
        interaction = AsyncMock()
        interaction.response = AsyncMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = AsyncMock()
        interaction.followup.send = AsyncMock()
        return interaction

    @pytest.mark.asyncio
    async def test_personal_expense_includes_description(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test /clerk personal includes description in Google Sheets row."""
        amount = 50.00
        description = "Grocery shopping at local market"

        await clerk_cog.personal(mock_interaction, amount, description)

        # Verify interaction was deferred
        mock_interaction.response.defer.assert_called_once()

        # Verify append_row was called
        mock_sheets_service.append_row.assert_called_once()
        call_args = mock_sheets_service.append_row.call_args[0]

        assert call_args[0] == "personal"  # Sheet name

        # Verify row structure: [Date, Time, Amount, Category, Month, submitted_by, Description]
        row_data = call_args[1]
        assert len(row_data) == 7  # Should have 7 columns
        assert row_data[2] == amount  # Amount at index 2
        assert row_data[3] == "personal"  # Category at index 3
        assert row_data[5] == "Test Bot"  # submitted_by at index 5
        assert row_data[6] == description  # Description at index 6 (last column)

        # Verify response was sent
        mock_interaction.followup.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_utilities_expense_includes_description(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test /clerk utilities includes description in Google Sheets row."""
        amount = 120.50
        description = "Monthly internet bill"

        await clerk_cog.utilities(mock_interaction, amount, description)

        # Verify append_row was called with correct structure
        mock_sheets_service.append_row.assert_called_once()
        call_args = mock_sheets_service.append_row.call_args[0]

        assert call_args[0] == "utilities"  # Sheet name

        row_data = call_args[1]
        assert len(row_data) == 7
        assert row_data[2] == amount
        assert row_data[3] == "utilities"  # Category at index 3
        assert row_data[6] == description  # Description at index 6 (last column)

    @pytest.mark.asyncio
    async def test_transport_expense_includes_description(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test /clerk transport includes description in Google Sheets row."""
        amount = 65.00
        description = "Gas for commute"

        await clerk_cog.transport(mock_interaction, amount, description)

        mock_sheets_service.append_row.assert_called_once()
        call_args = mock_sheets_service.append_row.call_args[0]

        assert call_args[0] == "transport"
        row_data = call_args[1]
        assert row_data[3] == "transport"  # Category at index 3
        assert row_data[6] == description  # Description at index 6

    @pytest.mark.asyncio
    async def test_extraordinary_expense_includes_description(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test /clerk extraordinary includes description in Google Sheets row."""
        amount = 500.00
        description = "Emergency car repair"

        await clerk_cog.extraordinary(mock_interaction, amount, description)

        mock_sheets_service.append_row.assert_called_once()
        call_args = mock_sheets_service.append_row.call_args[0]

        assert call_args[0] == "extraordinary"
        row_data = call_args[1]
        assert row_data[3] == "extraordinary"  # Category at index 3
        assert row_data[6] == description  # Description at index 6

    @pytest.mark.asyncio
    async def test_special_treat_default_description(
        self, clerk_cog, mock_interaction, mock_sheets_service, mock_budget_storage
    ):
        """Test /clerk special_treat with default description."""
        amount = 25.00

        await clerk_cog.special_treat(mock_interaction, amount)

        # Verify append_row was called
        mock_sheets_service.append_row.assert_called_once()
        call_args = mock_sheets_service.append_row.call_args[0]

        assert call_args[0] == "eat_out"  # Sheet name

        # Verify row structure: [Date, Time, Amount, Category, Month, Description]
        row_data = call_args[1]
        assert len(row_data) == 6  # eat_out has 6 columns (no submitted_by)
        assert row_data[2] == amount  # Amount at index 2
        assert row_data[3] == "Eating out / Takeaway"  # Category at index 3
        assert row_data[5] == "Eating out / Takeaway drink"  # Default description at index 5

        # Verify BudgetEntry was created with default description
        mock_budget_storage.save_entry.assert_called_once()
        saved_entry = mock_budget_storage.save_entry.call_args[0][0]
        assert isinstance(saved_entry, BudgetEntry)
        assert saved_entry.description == "Eating out / Takeaway drink"

    @pytest.mark.asyncio
    async def test_special_treat_custom_description(
        self, clerk_cog, mock_interaction, mock_sheets_service, mock_budget_storage
    ):
        """Test /clerk special_treat with custom description."""
        amount = 45.00
        description = "Birthday dinner at Italian restaurant"

        await clerk_cog.special_treat(mock_interaction, amount, description)

        # Verify append_row was called with custom description
        mock_sheets_service.append_row.assert_called_once()
        call_args = mock_sheets_service.append_row.call_args[0]

        row_data = call_args[1]
        assert row_data[5] == description  # Custom description at index 5 (last column)

        # Verify BudgetEntry was created with custom description
        saved_entry = mock_budget_storage.save_entry.call_args[0][0]
        assert saved_entry.description == description

    @pytest.mark.asyncio
    async def test_month_column_index_in_formula_rebuilding(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test that formula rebuilding uses correct month column index (5, not 4)."""
        amount = 30.00
        description = "Test expense"

        await clerk_cog.personal(mock_interaction, amount, description)

        # Verify rebuild_formula_from_sheet was called with correct parameters
        mock_sheets_service.rebuild_formula_from_sheet.assert_called_once()
        call_args = mock_sheets_service.rebuild_formula_from_sheet.call_args[0]

        # Verify correct sheet name and category
        assert call_args[0] == "personal"
        assert call_args[1] == "personal"

        # The month should be in YYYY-MM format
        month_arg = call_args[2]
        assert len(month_arg) == 7  # YYYY-MM format
        assert month_arg.count("-") == 1

    def test_budget_entry_model_has_description_field(self):
        """Test that BudgetEntry model has description field with default."""
        from bot.models import BudgetEntry

        entry = BudgetEntry(
            date=datetime.now(), amount=50.0, month="2026-01"
        )

        # Should have description field with default value
        assert hasattr(entry, "description")
        assert entry.description == "Eating out / Takeaway drink"

    def test_budget_entry_model_custom_description(self):
        """Test that BudgetEntry model accepts custom description."""
        from bot.models import BudgetEntry

        custom_desc = "Lunch with colleagues"
        entry = BudgetEntry(
            date=datetime.now(), amount=50.0, description=custom_desc, month="2026-01"
        )

        assert entry.description == custom_desc

    @pytest.mark.asyncio
    async def test_error_message_includes_description_column(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test that error messages show updated column structure."""
        amount = 50.00
        description = "Test"

        # Make append_row raise an exception
        mock_sheets_service.append_row.side_effect = Exception("Test error")

        await clerk_cog.personal(mock_interaction, amount, description)

        # Verify error message was sent
        mock_interaction.followup.send.assert_called_once()
        error_message = mock_interaction.followup.send.call_args[0][0]

        # Error message should include column structure with Description at the end
        assert "Description" in error_message
        assert (
            "[Date, Time, Amount, Category, Month, submitted_by, Description]"
            in error_message
        )
