"""Discord Receipt Bot - Main entry point."""
import asyncio
import logging

import discord
from discord.ext import commands

from bot.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')


class ReceiptBot(commands.Bot):
    """Custom bot class for the Receipt Bot."""
    
    def __init__(self):
        # Define intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.initial_extensions = [
            'bot.cogs.receipt',
            'bot.cogs.guess',
            'bot.cogs.clerk',
        ]
    
    async def setup_hook(self):
        """Setup hook to load extensions and sync commands."""
        logger.info("Loading extensions...")
        
        # Load all cogs
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
        
        # Sync commands to the guild
        try:
            guild = discord.Object(id=settings.guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} commands to guild {settings.guild_id}")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready."""
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
        await ctx.send(f"❌ An error occurred: {str(error)}")


async def main():
    """Main function to run the bot."""
    try:
        # Create bot instance
        bot = ReceiptBot()
        
        # Run the bot
        logger.info("Starting bot...")
        await bot.start(settings.discord_token)
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if 'bot' in locals():
            await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
