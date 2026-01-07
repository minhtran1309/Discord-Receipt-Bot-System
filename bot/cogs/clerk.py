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
        name="sync", description="Sync verified receipts to Google Sheets"
    )
    async def sync(self, interaction: discord.Interaction):
        """Sync verified receipts to Google Sheets."""
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

            # Sync to sheets
            count, synced_filenames = self.sheets.sync_multiple(receipts)

            # Mark receipts as synced
            for filename in synced_filenames:
                self.storage.mark_receipt_synced(filename)

            print(f"[Clerk Sync] Successfully synced {count} receipts")

            # Create detailed embed
            embed = discord.Embed(
                title="✅ Sync Complete",
                color=0x00FF00,
            )
            embed.add_field(
                name="Newly Synced",
                value=f"{count} receipts",
                inline=True
            )
            embed.add_field(
                name="Already Synced",
                value=f"{already_synced} receipts",
                inline=True
            )
            embed.add_field(
                name="Total Verified",
                value=f"{count + already_synced} receipts",
                inline=True
            )

            if count > 0:
                embed.description = "New data has been added to Google Sheets."
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

    @clerk_group.command(
        name="status",
        description="Check sync status of receipts"
    )
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
            color=0x3498db,
        )
        embed.add_field(
            name="✅ Synced to Sheets",
            value=f"{verified_synced} receipts",
            inline=False
        )
        embed.add_field(
            name="⏳ Verified (Not Synced)",
            value=f"{verified_unsynced} receipts",
            inline=False
        )
        embed.add_field(
            name="⏸️ Unverified",
            value=f"{unverified} receipts",
            inline=False
        )
        embed.add_field(
            name="📁 Total Receipts",
            value=f"{total} receipts",
            inline=False
        )

        if verified_unsynced > 0:
            embed.description = f"**{verified_unsynced} receipts** ready to sync. Use `/clerk sync` to sync them."
        else:
            embed.description = "All verified receipts are synced!"

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    pass
