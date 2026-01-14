"""Receipt processing cog - handles /receipt commands."""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from bot.services.ocr import OCRService
from bot.services.ai_extractor import AIExtractor
from bot.services.guesser import ItemGuesser
from bot.storage import Storage
from bot.budget_storage import BudgetStorage
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
        self.budget_storage = BudgetStorage()

    receipt_group = app_commands.Group(
        name="receipt", description="Receipt processing commands"
    )

    def _format_items_toon(self, items: list[ReceiptItem], max_items: int = 10) -> str:
        """Format receipt items in TOON (readable list) format.

        Args:
            items: List of ReceiptItem objects
            max_items: Maximum number of items to display (default: 10)

        Returns:
            Formatted string for Discord embed
        """
        if not items:
            return "No items found"

        lines = []

        for idx, item in enumerate(items[:max_items], start=1):
            # Confidence emoji
            if item.confidence is not None:
                if item.confidence >= 0.90:
                    conf_emoji = "✅"
                elif item.confidence >= 0.70:
                    conf_emoji = "⚠️"
                else:
                    conf_emoji = "❌"
                conf_str = f"{conf_emoji} ({item.confidence:.0%})"
            else:
                conf_str = "N/A"

            # Item name (prefer confirmed_name, then guessed_name, fallback to raw_name)
            display_name = item.confirmed_name or item.guessed_name or item.raw_name

            # Build item line
            lines.append(f"**{idx}. {display_name}** | {item.category}")

            # Quantity and unit
            if item.quantity != 1 or item.unit != "ea":
                lines.append(f"   ├─ Qty: {item.quantity} {item.unit}")

            # Price with discount
            if item.discount > 0:
                original_price = item.price + item.discount
                lines.append(f"   ├─ Price: ~~${original_price:.2f}~~ ${item.price:.2f} (saved ${item.discount:.2f})")
            else:
                lines.append(f"   ├─ Price: ${item.price:.2f}")

            # Confidence score
            lines.append(f"   └─ Confidence: {conf_str}")

            # Add spacing between items
            if idx < min(len(items), max_items):
                lines.append("")

        # Add "more items" indicator
        if len(items) > max_items:
            lines.append(f"_... and {len(items) - max_items} more items_")

        return "\n".join(lines)

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
            ocr_text = await self.ocr_service.process_image(
                image_bytes,
                openrouter_key=self.config.openrouter_api_key,
                fallback_model=self.config.fallback_ocr_model
            )

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

            # Step 6: Send final result with TOON format
            embed = discord.Embed(
                title="✅ Receipt Processed & Items Guessed",
                color=0x00FF00,
            )

            # Summary statistics
            embed.add_field(name="Store", value=parsed.store, inline=True)
            embed.add_field(name="Total Items", value=len(parsed.items), inline=True)
            embed.add_field(name="Total", value=f"${parsed.total:.2f}", inline=True)
            embed.add_field(name="Saved as", value=f"`{filename}`", inline=False)

            # Items in TOON format
            if parsed.items:
                items_display = self._format_items_toon(parsed.items, max_items=15)
                embed.add_field(name="📋 Items Details", value=items_display, inline=False)

            # Show needs review warning if applicable
            if needs_review > 0:
                embed.add_field(
                    name="⚠️ Low Confidence Items",
                    value=(
                        f"{needs_review} items need review.\n"
                        f"Use `/receipt correct_name <item_number> <new_name>` to fix."
                    ),
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
        """Show details of a specific receipt with TOON format."""
        receipt = self.storage.load_receipt(filename)

        if not receipt:
            await interaction.response.send_message("Receipt not found.")
            return

        embed = discord.Embed(
            title=f"🧾 Receipt: {receipt.store}",
            description=f"**Date**: {receipt.datetime.strftime('%Y-%m-%d %H:%M')}",
            color=0x00FF00 if receipt.verified else 0xFFFF00,
        )

        # Summary fields
        embed.add_field(name="Total Items", value=len(receipt.items), inline=True)
        embed.add_field(name="Total", value=f"${receipt.total:.2f}", inline=True)
        embed.add_field(
            name="Status",
            value="✓ Verified" if receipt.verified else "⏳ Unverified",
            inline=True
        )

        # Add items in TOON format
        items_display = self._format_items_toon(receipt.items, max_items=10)
        embed.add_field(name="📋 Items", value=items_display, inline=False)

        # Show subtotal, tax, discount if available
        details = []
        if receipt.subtotal:
            details.append(f"Subtotal: ${receipt.subtotal:.2f}")
        if receipt.tax:
            details.append(f"Tax: ${receipt.tax:.2f}")
        if receipt.discount_total and receipt.discount_total > 0:
            details.append(f"Discount: -${receipt.discount_total:.2f}")

        if details:
            embed.add_field(name="💵 Breakdown", value="\n".join(details), inline=False)

        # Show filename at bottom
        embed.set_footer(text=f"File: {filename}")

        await interaction.response.send_message(embed=embed)

    @receipt_group.command(name="verify", description="Mark receipt as verified")
    async def verify(self, interaction: discord.Interaction, filename: str):
        """Mark a receipt as verified and check for budget warnings."""
        receipt = self.storage.load_receipt(filename)

        if not receipt:
            await interaction.response.send_message("Receipt not found.")
            return

        receipt.verified = True
        self.storage.save_receipt(receipt)

        # Check eating out budget for overspending
        now = datetime.now()
        month = now.strftime("%Y-%m")
        budget = self.budget_storage.get_monthly_budget(month)

        # Create response with budget warning if needed
        response = f"Receipt `{filename}` marked as verified."

        if budget.overspent:
            response += (
                f"\n\n⚠️ **Budget Alert**: You've overspent your eating out budget "
                f"by **${abs(budget.remaining):.2f}** this month ({month}).\n"
                f"**Budget**: ${budget.budget_limit:.2f} | "
                f"**Spent**: ${budget.spent:.2f}"
            )

        await interaction.response.send_message(response)

    @receipt_group.command(name="delete", description="Delete a receipt")
    async def delete(self, interaction: discord.Interaction, filename: str):
        """Delete a stored receipt."""
        success = self.storage.delete_receipt(filename)

        if success:
            await interaction.response.send_message(f"Receipt `{filename}` deleted.")
        else:
            await interaction.response.send_message("Receipt not found.")

    @receipt_group.command(
        name="correct_name",
        description="Correct an item's name"
    )
    async def correct_name(
        self,
        interaction: discord.Interaction,
        filename: str,
        item_index: int,
        new_name: str
    ):
        """Correct an item's guessed name.

        Args:
            filename: Receipt filename
            item_index: Item number from the list (1-based)
            new_name: Corrected item name
        """
        await interaction.response.defer()

        # Load receipt
        receipt = self.storage.load_receipt(filename)
        if not receipt:
            await interaction.followup.send("❌ Receipt not found.")
            return

        # Validate item index
        if item_index < 1 or item_index > len(receipt.items):
            await interaction.followup.send(
                f"❌ Invalid item index. Must be between 1 and {len(receipt.items)}."
            )
            return

        # Get item (convert to 0-based index)
        item = receipt.items[item_index - 1]
        old_name = item.guessed_name or item.raw_name

        # Update item
        item.confirmed_name = new_name
        item.confidence = 1.0  # User confirmed, so 100% confidence
        item.needs_review = False

        # Save correction to corrections.json for future use
        self.storage.save_correction(item.raw_name, receipt.store, new_name)

        # Update guesser's cache
        key = f"{item.raw_name}|{receipt.store}"
        self.guesser.corrections[key] = new_name

        # Save updated receipt
        self.storage.save_receipt(receipt)

        # Send confirmation
        embed = discord.Embed(
            title="✅ Name Corrected",
            color=0x00FF00
        )
        embed.add_field(
            name="Item",
            value=f"**{item_index}. {item.raw_name}**",
            inline=False
        )
        embed.add_field(name="Old Name", value=old_name, inline=True)
        embed.add_field(name="New Name", value=new_name, inline=True)
        embed.add_field(
            name="Note",
            value=f"Correction saved to `corrections.json` for future receipts from {receipt.store}",
            inline=False
        )

        await interaction.followup.send(embed=embed)

    @receipt_group.command(
        name="correct_price",
        description="Correct an item's price"
    )
    async def correct_price(
        self,
        interaction: discord.Interaction,
        filename: str,
        item_index: int,
        new_price: float
    ):
        """Correct an item's price.

        Args:
            filename: Receipt filename
            item_index: Item number from the list (1-based)
            new_price: Corrected price
        """
        await interaction.response.defer()

        # Load receipt
        receipt = self.storage.load_receipt(filename)
        if not receipt:
            await interaction.followup.send("❌ Receipt not found.")
            return

        # Validate item index
        if item_index < 1 or item_index > len(receipt.items):
            await interaction.followup.send(
                f"❌ Invalid item index. Must be between 1 and {len(receipt.items)}."
            )
            return

        # Validate price
        if new_price <= 0:
            await interaction.followup.send("❌ Price must be greater than 0.")
            return

        # Get item
        item = receipt.items[item_index - 1]
        old_price = item.price

        # Update item price
        item.price = new_price

        # Recalculate receipt total
        receipt.total = sum(i.price * i.quantity for i in receipt.items)

        # Save updated receipt
        self.storage.save_receipt(receipt)

        # Send confirmation
        embed = discord.Embed(
            title="✅ Price Corrected",
            color=0x00FF00
        )
        embed.add_field(
            name="Item",
            value=f"**{item_index}. {item.guessed_name or item.raw_name}**",
            inline=False
        )
        embed.add_field(name="Old Price", value=f"${old_price:.2f}", inline=True)
        embed.add_field(name="New Price", value=f"${new_price:.2f}", inline=True)
        embed.add_field(
            name="New Total",
            value=f"${receipt.total:.2f}",
            inline=False
        )

        await interaction.followup.send(embed=embed)

    @receipt_group.command(
        name="correct_category",
        description="Correct an item's category"
    )
    async def correct_category(
        self,
        interaction: discord.Interaction,
        filename: str,
        item_index: int,
        new_category: str
    ):
        """Correct an item's category.

        Args:
            filename: Receipt filename
            item_index: Item number from the list (1-based)
            new_category: New category (Produce, Meat, Dairy, Bakery, Pantry, Frozen, Beverage, Household, Other)
        """
        await interaction.response.defer()

        # Valid categories
        valid_categories = [
            "Produce", "Meat", "Dairy", "Bakery", "Pantry",
            "Frozen", "Beverage", "Household", "Other"
        ]

        # Validate category
        if new_category not in valid_categories:
            await interaction.followup.send(
                f"❌ Invalid category. Must be one of: {', '.join(valid_categories)}"
            )
            return

        # Load receipt
        receipt = self.storage.load_receipt(filename)
        if not receipt:
            await interaction.followup.send("❌ Receipt not found.")
            return

        # Validate item index
        if item_index < 1 or item_index > len(receipt.items):
            await interaction.followup.send(
                f"❌ Invalid item index. Must be between 1 and {len(receipt.items)}."
            )
            return

        # Get item
        item = receipt.items[item_index - 1]
        old_category = item.category

        # Update category
        item.category = new_category

        # Save updated receipt
        self.storage.save_receipt(receipt)

        # Send confirmation
        embed = discord.Embed(
            title="✅ Category Corrected",
            color=0x00FF00
        )
        embed.add_field(
            name="Item",
            value=f"**{item_index}. {item.guessed_name or item.raw_name}**",
            inline=False
        )
        embed.add_field(name="Old Category", value=old_category, inline=True)
        embed.add_field(name="New Category", value=new_category, inline=True)

        await interaction.followup.send(embed=embed)

    @receipt_group.command(name="view_store", description="View store purchases by month or year")
    async def view_store(
        self,
        interaction: discord.Interaction,
        store: str,
        period: str = None,
    ):
        """View all TSV file contents for a specific store and time period.

        Args:
            store: Store name (e.g., "ALDI", "Woolworths")
            period: Time period in YYYY-MM (month) or YYYY (year) format. Leave empty for all time.

        Examples:
            /receipt view_store store:ALDI period:2026-01
            /receipt view_store store:Woolworths period:2026
            /receipt view_store store:IGA
        """
        await interaction.response.defer()

        from pathlib import Path
        import csv
        from datetime import datetime

        try:
            # Get items directory
            items_dir = Path(self.storage.data_dir) / "items"
            if not items_dir.exists():
                await interaction.followup.send("❌ No purchase data found.")
                return

            # Find all TSV files for this store
            store_normalized = store.lower().replace(" ", "_")
            all_tsv_files = sorted(items_dir.glob("*.tsv"))

            # Filter by store and period
            matching_files = []
            for tsv_file in all_tsv_files:
                # Check if store name is in filename
                if store_normalized not in tsv_file.name.lower():
                    continue

                # Extract date from filename (format: YYYY-MM-DD_HHMM_store_items.tsv)
                try:
                    date_part = tsv_file.name.split("_")[0]  # YYYY-MM-DD
                    file_date = datetime.strptime(date_part, "%Y-%m-%d")

                    # Filter by period if specified
                    if period:
                        if len(period) == 4:  # Year only (YYYY)
                            if file_date.year != int(period):
                                continue
                        elif len(period) == 7:  # Year-Month (YYYY-MM)
                            if file_date.strftime("%Y-%m") != period:
                                continue
                        else:
                            await interaction.followup.send("❌ Invalid period format. Use YYYY-MM or YYYY")
                            return

                    matching_files.append(tsv_file)
                except (ValueError, IndexError):
                    continue

            if not matching_files:
                period_text = f" for {period}" if period else ""
                await interaction.followup.send(f"❌ No purchases found for {store}{period_text}")
                return

            # Read and aggregate all items
            all_items = []
            total_spent = 0.0

            for tsv_file in matching_files:
                with open(tsv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f, delimiter="\t")
                    for row in reader:
                        all_items.append(row)
                        try:
                            price = float(row.get("price", 0))
                            total_spent += price
                        except ValueError:
                            pass

            if not all_items:
                await interaction.followup.send(f"❌ No items found in TSV files")
                return

            # Create summary statistics
            period_text = f" ({period})" if period else " (All Time)"
            category_totals = {}
            for item in all_items:
                category = item.get("category", "Other")
                try:
                    price = float(item.get("price", 0))
                    category_totals[category] = category_totals.get(category, 0) + price
                except ValueError:
                    pass

            # Create embed
            embed = discord.Embed(
                title=f"📊 {store} Purchases{period_text}",
                color=0x3498db,
                timestamp=datetime.now()
            )

            # Summary stats
            embed.add_field(
                name="Summary",
                value=f"**Total Items:** {len(all_items)}\n"
                      f"**Total Spent:** ${total_spent:.2f}\n"
                      f"**Receipts:** {len(matching_files)}",
                inline=False
            )

            # Category breakdown
            if category_totals:
                category_text = "\n".join(
                    f"• {cat}: ${amt:.2f}"
                    for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
                )
                embed.add_field(
                    name="💰 By Category",
                    value=category_text[:1024],  # Discord field limit
                    inline=False
                )

            # Recent items (last 10)
            recent_items = all_items[-10:] if len(all_items) > 10 else all_items
            items_text = "\n".join(
                f"• **{item.get('raw_name', 'Unknown')[:30]}** - ${item.get('price', '0')}\n"
                f"  _{item.get('category', 'Other')}_ | {item.get('date', 'N/A')}"
                for item in reversed(recent_items)
            )
            embed.add_field(
                name=f"🛒 Recent Items (Last {len(recent_items)})",
                value=items_text[:1024] if items_text else "None",
                inline=False
            )

            # Top items by spending
            item_spending = {}
            for item in all_items:
                name = item.get("guessed_name") or item.get("raw_name", "Unknown")
                try:
                    price = float(item.get("price", 0))
                    item_spending[name] = item_spending.get(name, 0) + price
                except ValueError:
                    pass

            if item_spending:
                top_items = sorted(item_spending.items(), key=lambda x: x[1], reverse=True)[:5]
                top_text = "\n".join(
                    f"• {name[:35]}: ${total:.2f}"
                    for name, total in top_items
                )
                embed.add_field(
                    name="🏆 Top Items by Spending",
                    value=top_text[:1024],
                    inline=False
                )

            embed.set_footer(text=f"Data from {len(matching_files)} receipt(s)")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error reading purchase data: {e}")

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
