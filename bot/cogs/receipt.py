"""Receipt processing cog - handles /receipt commands."""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from bot.services.ocr import OCRService
from bot.services.ai_extractor import AIExtractor
from bot.services.guesser import ItemGuesser
from bot.storage import Storage
from bot.models import Receipt, ReceiptItem
from bot.config import Settings
import re


class ReceiptCog(commands.Cog):
    """Commands for processing and managing receipts."""

    def __init__(
        self,
        bot: commands.Bot,
        ocr_service: OCRService,
        storage: Storage,
        guesser: ItemGuesser,
        ai_extractor: AIExtractor,
        settings: Settings,
    ):
        """Initialize receipt cog."""
        self.bot = bot
        self.ocr_service = ocr_service
        self.storage = storage
        self.guesser = guesser
        self.ai_extractor = ai_extractor
        self.settings = settings

    receipt_group = app_commands.Group(
        name="receipt", description="Receipt processing commands"
    )

    @receipt_group.command(name="process", description="Upload and process a receipt image")
    async def process(
        self, interaction: discord.Interaction, image: discord.Attachment
    ):
        """Process a receipt image with OCR and automatically guess item names."""
        await interaction.response.defer()

        try:
            # Step 1: Download image
            image_bytes = await image.read()

            # Step 2: OCR
            await interaction.followup.send("🔍 Processing receipt with OCR...")
            ocr_text = await self.ocr_service.process_image(image_bytes)

            # Step 3: AI Extraction
            await interaction.followup.send("🤖 Extracting structured data...")
            extracted_data = await self.ai_extractor.extract_receipt_data(ocr_text)
            parsed = self.ai_extractor.convert_to_receipt(extracted_data, ocr_text)

            # Validate extracted data
            validation_issues = self._validate_receipt(parsed)
            if validation_issues:
                issues_text = "\n".join(f"• {issue}" for issue in validation_issues)
                await interaction.followup.send(f"⚠️ **Validation Issues:**\n{issues_text}")

            # Step 4: Save receipt (unguessed)
            filename = self.storage.save_receipt(parsed)

            # Step 5: AUTO-GUESS ITEMS
            await interaction.followup.send("🤖 Guessing item names...")

            # Load latest corrections
            corrections = self.storage.load_corrections()
            self.guesser.update_corrections(corrections)

            # Batch guess all items
            guess_results = await self.guesser.guess_batch(parsed.items, parsed.store)

            # Update items with guesses
            needs_review = 0
            for item, guess_result in zip(parsed.items, guess_results):
                item.guessed_name = guess_result.product_name
                item.confidence = guess_result.confidence

                # Mark for review if confidence is low
                if guess_result.confidence < self.settings.confidence_threshold:
                    item.needs_review = True
                    needs_review += 1

            # Save updated receipt with guesses
            self.storage.save_receipt(parsed)

            # Save items to TSV file
            self._save_items_to_tsv(parsed)

            # Step 6: Send final result with table
            embed = discord.Embed(
                title="✅ Receipt Processed & Items Guessed",
                color=0x00FF00,
            )
            embed.add_field(name="Store", value=parsed.store, inline=True)
            embed.add_field(name="Total", value=f"${parsed.total:.2f}", inline=True)
            embed.add_field(name="Items", value=len(parsed.items), inline=True)
            embed.add_field(name="Needs Review", value=needs_review, inline=True)
            embed.add_field(name="Saved as", value=f"`{filename}`", inline=False)

            # Build table-like display of items
            if parsed.items:
                # Create table header
                table_lines = [
                    "```",
                    f"{'Raw Name':<20} {'Guessed Name':<25} {'Conf':<6} {'Review':<6}",
                    "-" * 63
                ]

                # Add each item as a row
                for item in parsed.items[:10]:  # Limit to first 10 items
                    raw = (item.raw_name[:18] + "..") if len(item.raw_name) > 20 else item.raw_name
                    guessed = (item.guessed_name[:23] + "..") if item.guessed_name and len(item.guessed_name) > 25 else (item.guessed_name or "N/A")
                    conf = f"{item.confidence:.2f}" if item.confidence is not None else "N/A"
                    review = "⚠️" if item.needs_review else "✓"

                    table_lines.append(f"{raw:<20} {guessed:<25} {conf:<6} {review:<6}")

                if len(parsed.items) > 10:
                    table_lines.append(f"\n... and {len(parsed.items) - 10} more items")

                table_lines.append("```")

                embed.add_field(
                    name="Items Details",
                    value="\n".join(table_lines),
                    inline=False
                )

            if needs_review > 0:
                embed.add_field(
                    name="⚠️ Low Confidence Items",
                    value=f"{needs_review} items need review. Use `/guess correct` to fix.",
                    inline=False
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error processing receipt: {e}")

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

        # Look for total (prioritize lines with just "total", not "subtotal")
        for line in lines:
            line_lower = line.lower()
            # Match "total" but not "subtotal"
            if line_lower.startswith("total") or " total " in line_lower or line_lower.endswith("total"):
                # Extract price from line (take the last match)
                matches = re.findall(r"\$?(\d+\.\d{2})", line)
                if matches:
                    total = float(matches[-1])
                    break  # Stop at first "total" match

        # Keywords to skip (not actual items)
        skip_keywords = [
            "total", "subtotal", "amount", "change", "rounding",
            "gst", "tax", "card", "eft", "credit", "debit",
            "sales", "payment", "net", "cash"
        ]

        # Basic item extraction (simplified)
        for line in lines:
            # Look for lines with prices
            matches = re.findall(r"(.+?)\s+\$?(\d+\.\d{2})", line)
            if matches:
                name, price = matches[0]
                price_float = float(price)

                # Skip if price is 0 or negative
                if price_float <= 0:
                    continue

                # Skip lines containing common non-item keywords
                if any(keyword in line.lower() for keyword in skip_keywords):
                    continue

                # Skip lines that look like dates (e.g., "30.12.25" or "02/01/2026")
                # Check if line contains date patterns: DD.MM.YY or MM/DD/YYYY
                if re.search(r'\d{1,2}[./]\d{1,2}[./]\d{2,4}', line):
                    continue

                # Skip lines that look like transaction codes or reference numbers
                # Lines starting with * or # followed by digits, or containing REF/TRANS/TERMINAL
                if re.search(r'^[*#]\d+|REF|TRANS|TERMINAL', line, re.IGNORECASE):
                    continue

                # Try to create ReceiptItem, skip if validation fails
                try:
                    items.append(
                        ReceiptItem(raw_name=name.strip(), price=price_float)
                    )
                except Exception:
                    # Skip invalid items silently
                    continue

        return Receipt(
            filename="",
            store=store,
            datetime=datetime.now(),
            raw_ocr_text=ocr_text,
            items=items,
            total=total,
        )

    def _validate_receipt(self, receipt: Receipt) -> list[str]:
        """Validate extracted receipt data.

        Args:
            receipt: Receipt object to validate

        Returns:
            List of validation issues (empty if no issues)
        """
        issues = []

        # Check if sum of item prices matches total
        items_sum = sum(item.price * item.quantity for item in receipt.items)
        if abs(items_sum - receipt.total) > 0.10:  # Allow 10 cent variance
            issues.append(
                f"Items sum (${items_sum:.2f}) doesn't match total (${receipt.total:.2f})"
            )

        # Check for missing critical fields
        if not receipt.store or receipt.store == "Unknown Store":
            issues.append("Store name not detected")

        if not receipt.items:
            issues.append("No items detected")

        return issues

    def _save_items_to_tsv(self, receipt: Receipt) -> None:
        """Save receipt items to a TSV file.

        Columns: raw_name, guessed_name, confidence, category, unit, price, discount, sku, store, date
        """
        from pathlib import Path

        # Create items directory if it doesn't exist
        items_dir = Path(self.storage.data_dir) / "items"
        items_dir.mkdir(parents=True, exist_ok=True)

        # Generate TSV filename based on receipt datetime and store
        tsv_filename = f"{receipt.datetime:%Y-%m-%d_%H%M}_{receipt.store.lower().replace(' ', '_')}_items.tsv"
        tsv_path = items_dir / tsv_filename

        # Write items to TSV
        with open(tsv_path, "w", encoding="utf-8") as f:
            # Write header
            f.write("raw_name\tguessed_name\tconfidence\tcategory\tunit\tprice\tdiscount\tsku\tstore\tdate\n")

            # Write each item
            for item in receipt.items:
                raw_name = item.raw_name or ""
                guessed_name = item.guessed_name or ""
                confidence = f"{item.confidence:.4f}" if item.confidence is not None else ""
                category = item.category or "Other"
                unit = item.unit or "ea"
                price = f"{item.price:.2f}"
                discount = f"{item.discount:.2f}" if item.discount else "0.00"
                sku = item.sku or ""
                store = receipt.store
                date = receipt.datetime.strftime("%Y-%m-%d")

                f.write(f"{raw_name}\t{guessed_name}\t{confidence}\t{category}\t{unit}\t{price}\t{discount}\t{sku}\t{store}\t{date}\n")


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    # This will be called from main.py with proper dependencies
    pass
