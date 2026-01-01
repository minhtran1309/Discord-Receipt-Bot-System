"""Receipt processing cog - handles /receipt commands."""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from bot.services.ocr import OCRService
from bot.storage import Storage
from bot.models import Receipt, ReceiptItem
import re


class ReceiptCog(commands.Cog):
    """Commands for processing and managing receipts."""

    def __init__(self, bot: commands.Bot, ocr_service: OCRService, storage: Storage):
        """Initialize receipt cog."""
        self.bot = bot
        self.ocr_service = ocr_service
        self.storage = storage

    receipt_group = app_commands.Group(
        name="receipt", description="Receipt processing commands"
    )

    @receipt_group.command(name="process", description="Upload and process a receipt image")
    async def process(
        self, interaction: discord.Interaction, image: discord.Attachment
    ):
        """Process a receipt image with OCR."""
        await interaction.response.defer()

        try:
            # Download image
            image_bytes = await image.read()

            # Process with OCR
            ocr_text = await self.ocr_service.process_image(image_bytes)

            # Parse receipt (basic implementation)
            parsed = self._parse_receipt(ocr_text)

            # Save to storage
            filename = self.storage.save_receipt(parsed)

            # Send response
            embed = discord.Embed(
                title="Receipt Processed",
                description=f"Saved as `{filename}`",
                color=0x00FF00,
            )
            embed.add_field(name="Store", value=parsed.store, inline=True)
            embed.add_field(
                name="Items", value=str(len(parsed.items)), inline=True
            )
            embed.add_field(name="Total", value=f"${parsed.total:.2f}", inline=True)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"Error processing receipt: {e}")

    @receipt_group.command(name="list", description="List all processed receipts")
    async def list_receipts(self, interaction: discord.Interaction):
        """List all stored receipts."""
        receipts = self.storage.list_receipts()

        if not receipts:
            await interaction.response.send_message("No receipts found.")
            return

        embed = discord.Embed(title="Stored Receipts", color=0x0000FF)
        receipt_list = "\n".join(f"• {r}" for r in receipts[:25])
        embed.description = receipt_list

        if len(receipts) > 25:
            embed.set_footer(text=f"Showing 25 of {len(receipts)} receipts")

        await interaction.response.send_message(embed=embed)

    @receipt_group.command(name="show", description="Display a specific receipt")
    async def show(self, interaction: discord.Interaction, filename: str):
        """Show details of a specific receipt."""
        receipt = self.storage.load_receipt(filename)

        if not receipt:
            await interaction.response.send_message("Receipt not found.")
            return

        embed = discord.Embed(
            title=f"Receipt: {receipt.store}",
            description=f"Date: {receipt.datetime.strftime('%Y-%m-%d %H:%M')}",
            color=0x00FF00 if receipt.verified else 0xFFFF00,
        )

        # Add items
        items_text = "\n".join(
            f"• {item.raw_name}: ${item.price:.2f}" for item in receipt.items[:10]
        )
        embed.add_field(name="Items", value=items_text or "None", inline=False)
        embed.add_field(name="Total", value=f"${receipt.total:.2f}", inline=True)
        embed.add_field(
            name="Verified", value="✓" if receipt.verified else "✗", inline=True
        )

        await interaction.response.send_message(embed=embed)

    @receipt_group.command(name="verify", description="Mark receipt as verified")
    async def verify(self, interaction: discord.Interaction, filename: str):
        """Mark a receipt as verified."""
        receipt = self.storage.load_receipt(filename)

        if not receipt:
            await interaction.response.send_message("Receipt not found.")
            return

        receipt.verified = True
        self.storage.save_receipt(receipt)

        await interaction.response.send_message(f"Receipt `{filename}` marked as verified.")

    @receipt_group.command(name="delete", description="Delete a receipt")
    async def delete(self, interaction: discord.Interaction, filename: str):
        """Delete a stored receipt."""
        success = self.storage.delete_receipt(filename)

        if success:
            await interaction.response.send_message(f"Receipt `{filename}` deleted.")
        else:
            await interaction.response.send_message("Receipt not found.")

    def _parse_receipt(self, ocr_text: str) -> Receipt:
        """Parse OCR text into a Receipt object (basic implementation)."""
        lines = [line.strip() for line in ocr_text.strip().split("\n") if line.strip()]

        # Simple heuristics for parsing
        store = lines[0] if lines else "Unknown Store"
        total = 0.0
        items = []

        # Look for total
        for line in lines:
            if "total" in line.lower():
                # Extract price from line
                matches = re.findall(r"\$?(\d+\.\d{2})", line)
                if matches:
                    total = float(matches[-1])

        # Basic item extraction (simplified)
        for line in lines:
            # Look for lines with prices
            matches = re.findall(r"(.+?)\s+\$?(\d+\.\d{2})", line)
            if matches and "total" not in line.lower():
                name, price = matches[0]
                items.append(
                    ReceiptItem(raw_name=name.strip(), price=float(price))
                )

        return Receipt(
            filename="",
            store=store,
            datetime=datetime.now(),
            raw_ocr_text=ocr_text,
            items=items,
            total=total,
        )


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    # This will be called from main.py with proper dependencies
    pass
