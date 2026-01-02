"""Item guessing cog - handles /guess commands."""

import discord
from discord import app_commands
from discord.ext import commands
from bot.services.guesser import ItemGuesser
from bot.storage import Storage
from bot.config import Settings


class GuessCog(commands.Cog):
    """Commands for AI-powered item name identification and corrections."""

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
        name="guess", description="Item name correction commands"
    )

    # REMOVED: /guess process command (now automatic after receipt processing)
    # REMOVED: /guess clear command

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
        """
        Save a manual correction for an item name.

        Args:
            raw_name: The abbreviated name from the receipt
            store: The store name
            actual_name: The correct full product name
        """
        await interaction.response.defer()

        # Save correction to storage
        self.storage.save_correction(raw_name, store, actual_name)

        # Update guesser's corrections cache
        key = f"{raw_name}|{store}"
        self.guesser.corrections[key] = actual_name

        embed = discord.Embed(
            title="Correction Saved",
            description=f"**{raw_name}** at **{store}** → **{actual_name}**",
            color=0x00FF00,
        )
        await interaction.followup.send(embed=embed)

    @guess_group.command(name="mappings", description="Show all learned corrections")
    async def mappings(self, interaction: discord.Interaction):
        """Display all learned item name corrections."""
        await interaction.response.defer()

        corrections = self.storage.load_corrections()

        if not corrections:
            await interaction.followup.send("No corrections saved yet.")
            return

        # Build embed with corrections (max 25 fields)
        embed = discord.Embed(
            title="Item Name Corrections",
            description=f"Total: {len(corrections)} corrections",
            color=0x3498DB,
        )

        # Show first 25 corrections
        for idx, (key, value) in enumerate(list(corrections.items())[:25]):
            raw_name, store = key.split("|")
            embed.add_field(
                name=f"{raw_name} @ {store}",
                value=value,
                inline=False,
            )

        if len(corrections) > 25:
            embed.set_footer(text=f"Showing 25 of {len(corrections)} corrections")

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    pass
