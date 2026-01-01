"""Item guessing cog - handles /guess commands."""

import discord
from discord import app_commands
from discord.ext import commands
from bot.services.guesser import ItemGuesser
from bot.storage import Storage
from bot.config import Settings


class GuessCog(commands.Cog):
    """Commands for AI-powered item name identification."""

    def __init__(
        self,
        bot: commands.Bot,
        guesser: ItemGuesser,
        storage: Storage,
        settings: Settings,
    ):
        """Initialize guess cog."""
        self.bot = bot
        self.guesser = guesser
        self.storage = storage
        self.settings = settings

    guess_group = app_commands.Group(
        name="guess", description="AI item identification commands"
    )

    @guess_group.command(
        name="process", description="Run AI guessing on a receipt's items"
    )
    async def process(self, interaction: discord.Interaction, filename: str):
        """Process all items in a receipt with AI guessing."""
        await interaction.response.defer()

        receipt = self.storage.load_receipt(filename)
        if not receipt:
            await interaction.followup.send("Receipt not found.")
            return

        # Load latest corrections
        corrections = self.storage.load_corrections()
        self.guesser.update_corrections(corrections)

        # Process each item
        processed = 0
        needs_review = 0

        for item in receipt.items:
            if not item.guessed_name:
                result = await self.guesser.guess(item.raw_name, receipt.store)
                item.guessed_name = result.product_name
                item.confidence = result.confidence

                if result.confidence < self.settings.confidence_threshold:
                    item.needs_review = True
                    needs_review += 1

                processed += 1

        # Save updated receipt
        self.storage.save_receipt(receipt)

        # Send response
        embed = discord.Embed(
            title="AI Guessing Complete", color=0x00FF00
        )
        embed.add_field(name="Processed", value=str(processed), inline=True)
        embed.add_field(name="Needs Review", value=str(needs_review), inline=True)

        if needs_review > 0:
            embed.description = (
                f"⚠️ {needs_review} items have low confidence and need review."
            )

        await interaction.followup.send(embed=embed)

    @guess_group.command(
        name="correct", description="Manually correct an item name"
    )
    async def correct(
        self,
        interaction: discord.Interaction,
        raw_name: str,
        store: str,
        actual_name: str,
    ):
        """Save a correction for future item guessing."""
        self.storage.save_correction(raw_name, store, actual_name)

        await interaction.response.send_message(
            f"✓ Learned: `{raw_name}` at {store} → `{actual_name}`"
        )

    @guess_group.command(name="mappings", description="Show all learned corrections")
    async def mappings(self, interaction: discord.Interaction):
        """Display all learned item name corrections."""
        corrections = self.storage.load_corrections()

        if not corrections:
            await interaction.response.send_message("No corrections learned yet.")
            return

        embed = discord.Embed(
            title="Learned Corrections",
            description=f"{len(corrections)} mappings",
            color=0x0000FF,
        )

        # Show first 25 corrections
        items = list(corrections.items())[:25]
        for key, value in items:
            raw, store = key.split("|")
            embed.add_field(
                name=f"{raw} ({store})",
                value=value,
                inline=False,
            )

        if len(corrections) > 25:
            embed.set_footer(text=f"Showing 25 of {len(corrections)} corrections")

        await interaction.response.send_message(embed=embed)

    @guess_group.command(name="clear", description="Clear a specific correction")
    async def clear(
        self, interaction: discord.Interaction, raw_name: str, store: str
    ):
        """Delete a correction mapping."""
        success = self.storage.delete_correction(raw_name, store)

        if success:
            await interaction.response.send_message(
                f"Cleared correction for `{raw_name}` at {store}"
            )
        else:
            await interaction.response.send_message("Correction not found.")


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    pass
