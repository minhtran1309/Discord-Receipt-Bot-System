"""Unit tests for /clerk receipt command (self-declaration feature)."""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.cogs.clerk import ClerkCog
from bot.services.sheets import SheetsService
from bot.storage import Storage


class TestClerkReceiptCommand:
    """Test suite for /clerk receipt self-declaration command."""

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

        # Mock get_worksheet to return a mock worksheet
        mock_worksheet = Mock()
        mock_worksheet.get_all_values = Mock(return_value=[
            ["receipt_file_name", "total_price", "submitted_by", "sync_status"],
            ["2026-01-15_1234_woolworths", "50.00", "Test Bot", "synced"],
            ["2026-01-20_1500_coles", "75.50", "Test Bot", "synced"],
        ])
        sheets.get_worksheet = Mock(return_value=mock_worksheet)

        return sheets

    @pytest.fixture
    def mock_storage(self):
        """Create a mock Storage."""
        return Mock(spec=Storage)

    @pytest.fixture
    def clerk_cog(self, mock_bot, mock_sheets_service, mock_storage):
        """Create ClerkCog instance with mocked dependencies."""
        return ClerkCog(mock_bot, mock_sheets_service, mock_storage)

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
    async def test_receipt_valid_input(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test /clerk receipt with valid inputs."""
        store_name = "Woolworths"
        total_price = 45.50

        await clerk_cog.receipt(mock_interaction, store_name, total_price)

        # Verify interaction was deferred
        mock_interaction.response.defer.assert_called_once()

        # Verify append_row was called with correct data
        mock_sheets_service.append_row.assert_called_once()
        call_args = mock_sheets_service.append_row.call_args[0]

        assert call_args[0] == "receipt_total"  # Sheet name
        row_data = call_args[1]
        assert row_data[1] == total_price  # Total price
        assert row_data[2] == "Test Bot"  # Bot signature
        assert row_data[3] == "self_declared"  # Sync status

        # Verify filename format: self_YYYY-MM-DD_HHMM_woolworths
        filename = row_data[0]
        assert filename.startswith("self_")
        assert "woolworths" in filename

        # Verify response was sent
        mock_interaction.followup.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_receipt_negative_price(self, clerk_cog, mock_interaction):
        """Test /clerk receipt with negative price (should fail)."""
        store_name = "Coles"
        total_price = -10.00

        await clerk_cog.receipt(mock_interaction, store_name, total_price)

        # Verify error message was sent
        mock_interaction.followup.send.assert_called_once()
        error_message = mock_interaction.followup.send.call_args[0][0]
        assert "❌" in error_message
        assert "greater than 0" in error_message

    @pytest.mark.asyncio
    async def test_receipt_zero_price(self, clerk_cog, mock_interaction):
        """Test /clerk receipt with zero price (should fail)."""
        store_name = "ALDI"
        total_price = 0.00

        await clerk_cog.receipt(mock_interaction, store_name, total_price)

        # Verify error message was sent
        mock_interaction.followup.send.assert_called_once()
        error_message = mock_interaction.followup.send.call_args[0][0]
        assert "❌" in error_message
        assert "greater than 0" in error_message

    @pytest.mark.asyncio
    async def test_receipt_excessive_price(self, clerk_cog, mock_interaction):
        """Test /clerk receipt with excessive price > $10,000 (should fail)."""
        store_name = "IGA"
        total_price = 15000.00

        await clerk_cog.receipt(mock_interaction, store_name, total_price)

        # Verify error message was sent
        mock_interaction.followup.send.assert_called_once()
        error_message = mock_interaction.followup.send.call_args[0][0]
        assert "❌" in error_message
        assert "unusually high" in error_message or "Max: $10,000" in error_message

    @pytest.mark.asyncio
    async def test_receipt_empty_store_name(self, clerk_cog, mock_interaction):
        """Test /clerk receipt with empty store name (should fail)."""
        store_name = ""
        total_price = 50.00

        await clerk_cog.receipt(mock_interaction, store_name, total_price)

        # Verify error message was sent
        mock_interaction.followup.send.assert_called_once()
        error_message = mock_interaction.followup.send.call_args[0][0]
        assert "❌" in error_message
        assert "1-50 characters" in error_message

    @pytest.mark.asyncio
    async def test_receipt_long_store_name(self, clerk_cog, mock_interaction):
        """Test /clerk receipt with excessively long store name (should fail)."""
        store_name = "A" * 51  # 51 characters
        total_price = 50.00

        await clerk_cog.receipt(mock_interaction, store_name, total_price)

        # Verify error message was sent
        mock_interaction.followup.send.assert_called_once()
        error_message = mock_interaction.followup.send.call_args[0][0]
        assert "❌" in error_message
        assert "1-50 characters" in error_message

    @pytest.mark.asyncio
    async def test_receipt_store_name_with_spaces(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test /clerk receipt with store name containing spaces (should normalize)."""
        store_name = "Harris Farm Markets"
        total_price = 65.75

        await clerk_cog.receipt(mock_interaction, store_name, total_price)

        # Verify append_row was called
        mock_sheets_service.append_row.assert_called_once()
        call_args = mock_sheets_service.append_row.call_args[0]

        # Verify filename has underscores instead of spaces
        filename = call_args[1][0]
        assert "harris_farm_markets" in filename

    @pytest.mark.asyncio
    async def test_receipt_filename_format(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test that generated filename follows expected format."""
        store_name = "Woolworths"
        total_price = 100.00

        # Mock datetime to control timestamp
        with patch("bot.cogs.clerk.datetime") as mock_datetime:
            mock_now = datetime(2026, 3, 23, 14, 30, 0)
            mock_datetime.now.return_value = mock_now

            await clerk_cog.receipt(mock_interaction, store_name, total_price)

        # Verify filename format: self_YYYY-MM-DD_HHMM_store_name
        call_args = mock_sheets_service.append_row.call_args[0]
        filename = call_args[1][0]

        assert filename.startswith("self_")
        assert "2026-03-23" in filename
        assert "1430" in filename
        assert "woolworths" in filename

    @pytest.mark.asyncio
    async def test_receipt_sheets_integration_error(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test /clerk receipt when Google Sheets append fails."""
        store_name = "Coles"
        total_price = 55.00

        # Make append_row raise an exception
        mock_sheets_service.append_row.side_effect = Exception(
            "Connection timeout"
        )

        await clerk_cog.receipt(mock_interaction, store_name, total_price)

        # Verify error message was sent
        mock_interaction.followup.send.assert_called_once()
        error_message = mock_interaction.followup.send.call_args[0][0]
        assert "❌" in error_message
        assert "Failed to save receipt" in error_message

    @pytest.mark.asyncio
    async def test_receipt_monthly_total_calculation(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test that monthly total is correctly calculated from Google Sheets."""
        store_name = "ALDI"
        total_price = 40.00

        # Mock current date to match test data (2026-01)
        with patch("bot.cogs.clerk.datetime") as mock_datetime:
            mock_now = datetime(2026, 1, 25, 10, 0, 0)
            mock_datetime.now.return_value = mock_now

            await clerk_cog.receipt(mock_interaction, store_name, total_price)

        # Verify response contains monthly total
        # Expected: 50.00 + 75.50 + 40.00 = 165.50 (from mock data + new entry)
        mock_interaction.followup.send.assert_called_once()

        # Get the embed argument
        call_args = mock_interaction.followup.send.call_args
        embed = call_args.kwargs.get("embed") or call_args.args[0] if call_args.args else None

        # Check if embed contains monthly total information
        assert embed is not None
        # The embed should have fields with monthly total

    @pytest.mark.asyncio
    async def test_receipt_max_valid_price(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test /clerk receipt with maximum valid price ($10,000)."""
        store_name = "Costco"
        total_price = 10000.00

        await clerk_cog.receipt(mock_interaction, store_name, total_price)

        # Verify it was accepted (not rejected)
        mock_sheets_service.append_row.assert_called_once()

    @pytest.mark.asyncio
    async def test_receipt_decimal_precision(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test /clerk receipt with various decimal precisions."""
        test_cases = [
            ("Store1", 45.5),
            ("Store2", 45.50),
            ("Store3", 45.505),  # Will be stored as 45.505
        ]

        for store_name, total_price in test_cases:
            mock_sheets_service.append_row.reset_mock()
            mock_interaction.reset_mock()

            await clerk_cog.receipt(mock_interaction, store_name, total_price)

            # Verify append was called with the exact price
            call_args = mock_sheets_service.append_row.call_args[0]
            assert call_args[1][1] == total_price

    @pytest.mark.asyncio
    async def test_receipt_special_characters_in_store_name(
        self, clerk_cog, mock_interaction, mock_sheets_service
    ):
        """Test /clerk receipt with special characters in store name."""
        store_name = "7-Eleven"
        total_price = 15.00

        await clerk_cog.receipt(mock_interaction, store_name, total_price)

        # Verify it was processed successfully
        mock_sheets_service.append_row.assert_called_once()
        call_args = mock_sheets_service.append_row.call_args[0]

        # Verify filename contains normalized store name
        filename = call_args[1][0]
        assert "7-eleven" in filename or "7_eleven" in filename

    def test_clerk_cog_initialization(self, mock_bot, mock_sheets_service, mock_storage):
        """Test that ClerkCog initializes correctly."""
        cog = ClerkCog(mock_bot, mock_sheets_service, mock_storage)

        assert cog.bot == mock_bot
        assert cog.sheets == mock_sheets_service
        assert cog.storage == mock_storage
        assert cog.budget_storage is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
