"""Clerk cog - handles /clerk commands for expense tracking."""

from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from bot.budget_storage import BudgetStorage
from bot.models import BudgetEntry
from bot.services.sheets import SheetsService
from bot.storage import Storage


class ClerkCog(commands.Cog):
    """Commands for expense aggregation and Google Sheets sync."""

    def __init__(self, bot: commands.Bot, sheets: SheetsService, storage: Storage):
        """Initialize clerk cog."""
        self.bot = bot
        self.sheets = sheets
        self.storage = storage
        self.budget_storage = BudgetStorage()

    clerk_group = app_commands.Group(
        name="clerk", description="Expense tracking and reporting commands"
    )

    @clerk_group.command(
        name="sync", description="Sync verified receipts to Google Sheets"
    )
    async def sync(self, interaction: discord.Interaction):
        """Sync verified receipts to Google Sheets with monthly aggregation."""
        await interaction.response.defer()

        try:
            # Load all receipts
            filenames = self.storage.list_receipts()
            print(f"[Clerk Sync] Found {len(filenames)} receipt files")

            # Filter for verified and unsynced receipts
            receipts = []
            already_synced = 0

            for f in filenames:
                receipt = self.storage.load_receipt(f)
                if not receipt:
                    continue

                if receipt.verified and not receipt.synced_to_sheets:
                    receipts.append(receipt)
                    print(f"[Clerk Sync] ✓ Verified & unsynced: {f}")
                elif receipt.verified and receipt.synced_to_sheets:
                    already_synced += 1
                    print(f"[Clerk Sync] ↻ Already synced: {f}")
                elif receipt:
                    print(f"[Clerk Sync] ✗ Unverified receipt: {f}")

            if not receipts:
                if already_synced > 0:
                    await interaction.followup.send(
                        f"✅ All verified receipts are already synced!\n\n"
                        f"**Already synced**: {already_synced} receipts\n\n"
                        f"Use `/receipt verify <filename>` to verify more receipts."
                    )
                else:
                    await interaction.followup.send(
                        "❌ No verified receipts to sync.\n\n"
                        "Use `/receipt verify <filename>` to verify receipts first."
                    )
                return

            print(f"[Clerk Sync] Syncing {len(receipts)} verified receipts...")

            # Step 1: Sync individual items to Sheet1 (existing behavior)
            count, synced_filenames = self.sheets.sync_multiple(receipts)
            print(f"[Clerk Sync] Synced {count} receipts to Sheet1")

            # Step 2: Sync receipt totals to receipt_total sheet (NEW)
            month_cell_refs = self.sheets.sync_receipt_totals(receipts)
            print(f"[Clerk Sync] Synced receipt totals to receipt_total sheet")

            # Step 3: Update monthly formulas in total_cost_monthly (NEW)
            self.sheets.update_shopping_expenses_formulas(month_cell_refs)
            print(f"[Clerk Sync] Updated shopping_expenses formulas")

            # Mark receipts as synced
            for filename in synced_filenames:
                self.storage.mark_receipt_synced(filename)

            print(f"[Clerk Sync] Successfully synced {count} receipts")

            # Create detailed embed
            embed = discord.Embed(
                title="✅ Sync Complete",
                color=0x00FF00,
            )
            embed.add_field(name="Newly Synced", value=f"{count} receipts", inline=True)
            embed.add_field(
                name="Already Synced", value=f"{already_synced} receipts", inline=True
            )
            embed.add_field(
                name="Total Verified",
                value=f"{count + already_synced} receipts",
                inline=True,
            )

            if count > 0:
                embed.description = (
                    "New data has been added to Google Sheets:\n"
                    "• Sheet1: Individual items\n"
                    "• receipt_total: Receipt totals\n"
                    "• total_cost_monthly: Updated formulas"
                )
            else:
                embed.description = "No new data to sync."

            await interaction.followup.send(embed=embed)

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            print(f"[Clerk Sync] Error during sync:\n{error_details}")
            await interaction.followup.send(
                f"❌ Error syncing to Google Sheets:\n```{str(e)}```\n\n"
                f"Check the bot console logs for more details."
            )

    @clerk_group.command(
        name="spent", description="Query spending on a specific product"
    )
    async def spent(
        self,
        interaction: discord.Interaction,
        product: str,
        month: str = None,
    ):
        """Calculate total spending on a product."""
        filenames = self.storage.list_receipts()
        receipts = [self.storage.load_receipt(f) for f in filenames]

        total = 0.0
        count = 0

        for receipt in receipts:
            if not receipt:
                continue

            # Filter by month if specified
            if month and not receipt.datetime.strftime("%Y-%m").startswith(month):
                continue

            for item in receipt.items:
                item_name = (
                    item.confirmed_name or item.guessed_name or item.raw_name
                ).lower()
                if product.lower() in item_name:
                    total += item.price * item.quantity
                    count += 1

        embed = discord.Embed(
            title=f"Spending on '{product}'",
            color=0x0000FF,
        )
        embed.add_field(name="Total Spent", value=f"${total:.2f}", inline=True)
        embed.add_field(name="Purchases", value=str(count), inline=True)

        if month:
            embed.description = f"For month: {month}"

        await interaction.response.send_message(embed=embed)

    @clerk_group.command(name="monthly", description="Get monthly expense summary")
    async def monthly(self, interaction: discord.Interaction, month: str = None):
        """Get expense summary for a month (YYYY-MM format)."""
        if not month:
            month = datetime.now().strftime("%Y-%m")

        filenames = self.storage.list_receipts()
        receipts = [self.storage.load_receipt(f) for f in filenames]

        total = 0.0
        receipt_count = 0
        item_count = 0

        for receipt in receipts:
            if not receipt:
                continue

            if receipt.datetime.strftime("%Y-%m") == month:
                total += receipt.total
                receipt_count += 1
                item_count += len(receipt.items)

        embed = discord.Embed(
            title=f"Monthly Summary: {month}",
            color=0x00FF00,
        )
        embed.add_field(name="Total Spent", value=f"${total:.2f}", inline=False)
        embed.add_field(name="Receipts", value=str(receipt_count), inline=True)
        embed.add_field(name="Items", value=str(item_count), inline=True)

        await interaction.response.send_message(embed=embed)

    @clerk_group.command(
        name="report", description="Generate expense report for a date range"
    )
    async def report(
        self,
        interaction: discord.Interaction,
        start_date: str,
        end_date: str,
    ):
        """Generate expense report between two dates (YYYY-MM-DD format)."""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            await interaction.response.send_message(
                "Invalid date format. Use YYYY-MM-DD."
            )
            return

        filenames = self.storage.list_receipts()
        receipts = [self.storage.load_receipt(f) for f in filenames]

        total = 0.0
        receipt_count = 0

        for receipt in receipts:
            if not receipt:
                continue

            if start <= receipt.datetime <= end:
                total += receipt.total
                receipt_count += 1

        embed = discord.Embed(
            title="Expense Report",
            description=f"{start_date} to {end_date}",
            color=0x0000FF,
        )
        embed.add_field(name="Total Spent", value=f"${total:.2f}", inline=False)
        embed.add_field(name="Receipts", value=str(receipt_count), inline=True)

        await interaction.response.send_message(embed=embed)

    @clerk_group.command(name="status", description="Check sync status of receipts")
    async def status(self, interaction: discord.Interaction):
        """Show sync status of all receipts."""
        await interaction.response.defer()

        filenames = self.storage.list_receipts()

        verified_synced = 0
        verified_unsynced = 0
        unverified = 0

        for f in filenames:
            receipt = self.storage.load_receipt(f)
            if not receipt:
                continue

            if receipt.verified and receipt.synced_to_sheets:
                verified_synced += 1
            elif receipt.verified:
                verified_unsynced += 1
            else:
                unverified += 1

        total = verified_synced + verified_unsynced + unverified

        embed = discord.Embed(
            title="📊 Receipt Sync Status",
            color=0x3498DB,
        )
        embed.add_field(
            name="✅ Synced to Sheets",
            value=f"{verified_synced} receipts",
            inline=False,
        )
        embed.add_field(
            name="⏳ Verified (Not Synced)",
            value=f"{verified_unsynced} receipts",
            inline=False,
        )
        embed.add_field(
            name="⏸️ Unverified", value=f"{unverified} receipts", inline=False
        )
        embed.add_field(
            name="📁 Total Receipts", value=f"{total} receipts", inline=False
        )

        if verified_unsynced > 0:
            embed.description = f"**{verified_unsynced} receipts** ready to sync. Use `/clerk sync` to sync them."
        else:
            embed.description = "All verified receipts are synced!"

        await interaction.followup.send(embed=embed)

    @clerk_group.command(
        name="special_treat", description="Log eating out or takeaway drink expense"
    )
    async def special_treat(self, interaction: discord.Interaction, amount: float):
        """Log an eating out expense and update budget tracking.

        Args:
            amount: Amount spent on eating out or takeaway drink
        """
        await interaction.response.defer()

        try:
            # Validate amount
            if amount <= 0:
                await interaction.followup.send("❌ Amount must be greater than 0")
                return

            # Get current date and month
            now = datetime.now()
            month = now.strftime("%Y-%m")

            # Create budget entry
            entry = BudgetEntry(date=now, amount=amount, month=month)

            # Save to local storage
            filename = self.budget_storage.save_entry(entry)
            print(f"[Budget] Saved entry: {filename}")

            # Update Google Sheets (eat_out_2026 tab)
            try:
                row = [
                    now.strftime("%Y-%m-%d"),  # Date
                    now.strftime("%H:%M"),  # Time
                    amount,  # Amount
                    "Eating out / Takeaway",  # Category
                    month,  # Month
                ]
                self.sheets.append_row("eat_out_2026", row)
                print(f"[Budget] Updated Google Sheets: eat_out_2026")
            except Exception as e:
                print(f"[Budget] Error updating Google Sheets: {e}")
                await interaction.followup.send(
                    f"⚠️ Entry saved locally but failed to sync to Google Sheets:\n```{e}```"
                )
                return

            # Get updated monthly budget
            budget = self.budget_storage.get_monthly_budget(month)

            # Create response embed
            embed = discord.Embed(
                title="🍔 Special Treat Logged",
                color=0x00FF00 if not budget.overspent else 0xFF0000,
                timestamp=now,
            )

            embed.add_field(name="Amount Spent", value=f"${amount:.2f}", inline=True)
            embed.add_field(
                name="Date", value=now.strftime("%Y-%m-%d %H:%M"), inline=True
            )

            embed.add_field(
                name=f"📊 {month} Budget Status",
                value=(
                    f"**Budget**: ${budget.budget_limit:.2f}\n"
                    f"**Spent**: ${budget.spent:.2f}\n"
                    f"**Remaining**: ${budget.remaining:.2f}"
                ),
                inline=False,
            )

            # Add overspending warning or surplus message
            if budget.overspent:
                embed.add_field(
                    name="⚠️ Budget Exceeded",
                    value=(
                        f"You've overspent by **${abs(budget.remaining):.2f}** this month!\n"
                        f"I'll remind you about this when you sync grocery receipts."
                    ),
                    inline=False,
                )
                embed.color = 0xFF0000  # Red
            elif budget.remaining > 0:
                embed.add_field(
                    name="✅ Under Budget",
                    value=(
                        f"Great! You have **${budget.remaining:.2f}** left for {month}.\n"
                        f"Unused budget will be added to Nov/Dec for holiday shopping!"
                    ),
                    inline=False,
                )

            # Show year-to-date surplus
            year_surplus = self.budget_storage.get_year_surplus(now.year)
            if year_surplus > 0:
                embed.add_field(
                    name="🎄 Holiday Shopping Fund",
                    value=f"**${year_surplus:.2f}** saved for Nov/Dec",
                    inline=False,
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            print(f"[Budget] Error: {error_details}")
            await interaction.followup.send(f"❌ Error logging special treat: {e}")

    @clerk_group.command(
        name="budget_status", description="Check eating out budget status"
    )
    async def budget_status(self, interaction: discord.Interaction, month: str = None):
        """Check eating out budget status for a specific month.

        Args:
            month: Month in YYYY-MM format (default: current month)
        """
        await interaction.response.defer()

        try:
            # Default to current month
            if not month:
                month = datetime.now().strftime("%Y-%m")

            # Validate format
            try:
                datetime.strptime(month, "%Y-%m")
            except ValueError:
                await interaction.followup.send(
                    "❌ Invalid month format. Use YYYY-MM (e.g., 2026-01)"
                )
                return

            # Get budget data
            budget = self.budget_storage.get_monthly_budget(month)

            # Create embed
            embed = discord.Embed(
                title=f"🍔 Eating Out Budget - {month}",
                color=0x00FF00 if not budget.overspent else 0xFF0000,
            )

            embed.add_field(
                name="💰 Budget Summary",
                value=(
                    f"**Budget**: ${budget.budget_limit:.2f}\n"
                    f"**Spent**: ${budget.spent:.2f}\n"
                    f"**Remaining**: ${budget.remaining:.2f}"
                ),
                inline=False,
            )

            # Show entries
            if budget.entries:
                entries_text = "\n".join(
                    f"• {entry.date:%Y-%m-%d %H:%M} - ${entry.amount:.2f}"
                    for entry in budget.entries[-10:]  # Last 10 entries
                )

                if len(budget.entries) > 10:
                    entries_text += f"\n\n... and {len(budget.entries) - 10} more"

                embed.add_field(
                    name=f"📝 Recent Entries ({len(budget.entries)} total)",
                    value=entries_text,
                    inline=False,
                )
            else:
                embed.add_field(
                    name="📝 Entries",
                    value="No eating out expenses logged this month",
                    inline=False,
                )

            # Show year surplus
            year = int(month.split("-")[0])
            year_surplus = self.budget_storage.get_year_surplus(year)
            if year_surplus > 0:
                embed.add_field(
                    name="🎄 Holiday Shopping Fund",
                    value=f"**${year_surplus:.2f}** saved for Nov/Dec",
                    inline=False,
                )

            # Add status message
            if budget.overspent:
                embed.description = (
                    f"⚠️ Budget exceeded by **${abs(budget.remaining):.2f}**"
                )
            elif budget.spent == 0:
                embed.description = "✨ No spending this month - full budget available!"
            else:
                embed.description = (
                    f"✅ **${budget.remaining:.2f}** remaining for this month"
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error checking budget status: {e}")

    @clerk_group.command(
        name="personal",
        description="Log personal expense without receipt"
    )
    async def personal(
        self,
        interaction: discord.Interaction,
        amount: float,
        description: str
    ):
        """Log a personal expense.

        Args:
            amount: Amount spent
            description: Description of expense
        """
        await self._log_expense(interaction, "personal", amount, description)

    @clerk_group.command(
        name="utilities",
        description="Log utilities expense without receipt"
    )
    async def utilities(
        self,
        interaction: discord.Interaction,
        amount: float,
        description: str
    ):
        """Log a utilities expense.

        Args:
            amount: Amount spent
            description: Description of expense
        """
        await self._log_expense(interaction, "utilities", amount, description)

    @clerk_group.command(
        name="transport",
        description="Log transport expense without receipt"
    )
    async def transport(
        self,
        interaction: discord.Interaction,
        amount: float,
        description: str
    ):
        """Log a transport expense.

        Args:
            amount: Amount spent
            description: Description of expense
        """
        await self._log_expense(interaction, "transport", amount, description)

    @clerk_group.command(
        name="extraordinary",
        description="Log extraordinary expense without receipt"
    )
    async def extraordinary(
        self,
        interaction: discord.Interaction,
        amount: float,
        description: str
    ):
        """Log an extraordinary expense.

        Args:
            amount: Amount spent
            description: Description of expense
        """
        await self._log_expense(interaction, "extraordinary", amount, description)

    async def _log_expense(
        self,
        interaction: discord.Interaction,
        category: str,
        amount: float,
        description: str
    ):
        """Internal method to log an expense.

        Args:
            interaction: Discord interaction
            category: Expense category (personal, utilities, transport, extraordinary)
            amount: Amount spent
            description: Expense description
        """
        await interaction.response.defer()

        try:
            # Validate amount
            if amount <= 0:
                await interaction.followup.send("❌ Amount must be greater than 0")
                return

            # Get current date and month
            now = datetime.now()
            month = now.strftime("%Y-%m")

            # Get bot signature from config
            bot_signature = self.bot.settings.bot_name if hasattr(self.bot, 'settings') else "Receipt Bot (Local)"

            # Append directly to Google Sheets (no local storage)
            try:
                # Sheet name: just category name (e.g., "personal", "utilities")
                # User created these sheets with structure: [Date, Time, Amount, Category, Month, submitted_by]
                sheet_name = category

                # Prepare row: [Date, Time, Amount, Category, Month, submitted_by]
                row = [
                    now.strftime("%Y-%m-%d"),  # Date
                    now.strftime("%H:%M"),     # Time
                    amount,                     # Amount
                    category,                   # Category
                    month,                      # Month
                    bot_signature               # submitted_by
                ]

                # Append to sheet
                self.sheets.append_row(sheet_name, row)
                print(f"[Expense] Appended to Google Sheets: {sheet_name}")

                # Rebuild formula from Google Sheets (source of truth)
                # This reads all rows for the month and generates complete formula
                new_formula = self.sheets.rebuild_formula_from_sheet(sheet_name, category, month, amount_column="C")
                print(f"[Expense] Rebuilt formula for {category}/{month}: {new_formula}")

                # Update total_cost_monthly with complete formula
                if new_formula:
                    worksheet = self.sheets.get_worksheet("total_cost_monthly")
                    category_row = self.sheets.find_or_create_category_row("total_cost_monthly", category)
                    month_col = self.sheets.find_or_create_month_column("total_cost_monthly", month)
                    worksheet.update_cell(category_row, month_col, new_formula)
                    print(f"[Expense] Updated total_cost_monthly formula for {category}/{month}")

            except Exception as e:
                print(f"[Expense] Error updating Google Sheets: {e}")
                await interaction.followup.send(
                    f"❌ Failed to sync to Google Sheets:\n```{e}```\n\n"
                    f"Please ensure the '{category}' sheet exists with correct structure:\n"
                    f"`[Date, Time, Amount, Category, Month, submitted_by]`"
                )
                return

            # Calculate monthly total by reading from Google Sheets
            try:
                worksheet = self.sheets.get_worksheet(sheet_name)
                all_records = worksheet.get_all_values()

                monthly_total = 0.0
                for row in all_records[1:]:  # Skip header
                    if len(row) > 4 and row[4] == month:  # Column E (index 4) is Month
                        try:
                            monthly_total += float(row[2])  # Column C (index 2) is Amount
                        except (ValueError, IndexError):
                            continue

            except Exception as e:
                print(f"[Expense] Error calculating monthly total: {e}")
                monthly_total = amount  # Fallback to just current amount

            # Create response embed
            embed = discord.Embed(
                title=f"💰 {category.title()} Expense Logged",
                color=0x00FF00,
                timestamp=now
            )

            embed.add_field(
                name="Amount",
                value=f"${amount:.2f}",
                inline=True
            )
            embed.add_field(
                name="Description",
                value=description,
                inline=True
            )
            embed.add_field(
                name=f"📊 {month} Total",
                value=f"${monthly_total:.2f}",
                inline=False
            )

            embed.description = f"✅ Expense logged and synced to Google Sheets"

            await interaction.followup.send(embed=embed)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[Expense] Error: {error_details}")
            await interaction.followup.send(
                f"❌ Error logging {category} expense: {e}"
            )


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    pass
