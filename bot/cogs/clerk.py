"""Clerk cog - handles /clerk commands for expense tracking."""

import discord
from discord import app_commands
from discord.ext import commands
from bot.services.sheets import SheetsService
from bot.storage import Storage
from datetime import datetime


class ClerkCog(commands.Cog):
    """Commands for expense aggregation and Google Sheets sync."""

    def __init__(self, bot: commands.Bot, sheets: SheetsService, storage: Storage):
        """Initialize clerk cog."""
        self.bot = bot
        self.sheets = sheets
        self.storage = storage

    clerk_group = app_commands.Group(
        name="clerk", description="Expense tracking and reporting commands"
    )

    @clerk_group.command(
        name="sync", description="Sync all verified receipts to Google Sheets"
    )
    async def sync(self, interaction: discord.Interaction):
        """Sync verified receipts to Google Sheets."""
        await interaction.response.defer()

        try:
            # Load all receipts
            filenames = self.storage.list_receipts()
            receipts = [
                self.storage.load_receipt(f)
                for f in filenames
                if self.storage.load_receipt(f) and self.storage.load_receipt(f).verified
            ]

            if not receipts:
                await interaction.followup.send("No verified receipts to sync.")
                return

            # Sync to sheets
            count = self.sheets.sync_multiple(receipts)

            embed = discord.Embed(
                title="Sync Complete",
                description=f"Synced {count} verified receipts to Google Sheets",
                color=0x00FF00,
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"Error syncing to Google Sheets: {e}")

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

    @clerk_group.command(
        name="monthly", description="Get monthly expense summary"
    )
    async def monthly(
        self, interaction: discord.Interaction, month: str = None
    ):
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


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    pass
