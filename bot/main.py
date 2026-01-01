"""Main entry point for the Discord Receipt Bot."""

import discord
from discord.ext import commands
import logging
from bot.config import get_settings
from bot.storage import Storage
from bot.services.ocr import OCRService
from bot.services.guesser import ItemGuesser
from bot.services.sheets import SheetsService
from bot.cogs.receipt import ReceiptCog
from bot.cogs.guess import GuessCog
from bot.cogs.clerk import ClerkCog


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ReceiptBot(commands.Bot):
    """Main bot class."""

    def __init__(self):
        """Initialize the bot."""
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

        # Load settings
        self.settings = get_settings()

        # Initialize services
        self.storage = Storage(self.settings.data_dir)
        self.ocr_service = OCRService(
            api_key=self.settings.mistral_api_key,
            model=self.settings.mistral_ocr_model,
        )
        self.guesser = ItemGuesser(
            self.settings.openrouter_api_key,
            self.settings.openrouter_model,
            self.storage.load_corrections(),
        )
        self.sheets_service = SheetsService(
            self.settings.google_credentials_path,
            self.settings.google_spreadsheet_id,
        )

    async def setup_hook(self):
        """Setup hook called when bot starts."""
        logger.info("Loading cogs...")

        # Add cogs with error handling
        cogs_to_load = [
            ("Receipt", ReceiptCog(self, self.ocr_service, self.storage)),
            ("Guess", GuessCog(self, self.guesser, self.storage, self.settings)),
            ("Clerk", ClerkCog(self, self.sheets_service, self.storage)),
        ]

        for name, cog in cogs_to_load:
            try:
                await self.add_cog(cog)
                logger.info(f"✓ Loaded {name} cog")
            except Exception as e:
                logger.error(f"✗ Failed to load {name} cog: {e}")

        # Sync commands
        try:
            if self.settings.discord_guild_id:
                guild = discord.Object(id=self.settings.discord_guild_id)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} commands to guild {self.settings.discord_guild_id}")
            else:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} commands globally")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        logger.info("Bot is ready!")

        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="receipts 📝"
            )
        )

    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        logger.error(f"Command error: {error}")

    async def close(self):
        """Cleanup when bot shuts down."""
        await self.ocr_service.close()
        await self.guesser.close()
        await super().close()


def main():
    """Run the bot."""
    try:
        settings = get_settings()
        bot = ReceiptBot()
        bot.run(settings.discord_token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    main()
