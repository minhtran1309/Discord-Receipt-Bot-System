"""Guess management cog with slash commands."""
import uuid
from datetime import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from bot.storage import load_guesses, add_guess, save_guesses


class GuessCog(commands.Cog):
    """Cog for managing spending guesses."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    guess_group = app_commands.Group(
        name="guess",
        description="Manage spending guesses"
    )
    
    @guess_group.command(name="process", description="Submit a guess for monthly spending")
    @app_commands.describe(
        amount="Your guess for the total spending amount",
        month="Month for the guess (optional, defaults to current month)",
        category="Category for the guess (optional)"
    )
    async def process_guess(
        self,
        interaction: discord.Interaction,
        amount: float,
        month: Optional[str] = None,
        category: Optional[str] = None
    ):
        """Submit a spending guess."""
        try:
            # Use current month if not provided
            if not month:
                month = datetime.now().strftime("%Y-%m")
            
            # Create guess
            guess_id = str(uuid.uuid4())[:8]
            guess_data = {
                'id': guess_id,
                'user_id': interaction.user.id,
                'username': interaction.user.name,
                'amount': amount,
                'month': month,
                'category': category,
                'timestamp': datetime.now().isoformat(),
                'is_correct': False,
                'actual_amount': None
            }
            
            # Save guess
            add_guess(guess_data)
            
            # Create response embed
            embed = discord.Embed(
                title="✅ Guess Submitted",
                description=f"Guess ID: `{guess_id}`",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Amount", value=f"${amount:.2f}", inline=True)
            embed.add_field(name="Month", value=month, inline=True)
            
            if category:
                embed.add_field(name="Category", value=category, inline=True)
            
            embed.set_footer(text=f"Submitted by {interaction.user.name}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error processing guess: {str(e)}",
                ephemeral=True
            )
    
    @guess_group.command(name="correct", description="Mark a guess as correct and set actual amount")
    @app_commands.describe(
        guess_id="The ID of the guess to mark as correct",
        actual_amount="The actual spending amount"
    )
    async def correct_guess(
        self,
        interaction: discord.Interaction,
        guess_id: str,
        actual_amount: float
    ):
        """Mark a guess as correct and set the actual amount."""
        guesses = load_guesses()
        
        # Find the guess
        guess = None
        guess_index = -1
        for i, g in enumerate(guesses):
            if g.get('id') == guess_id:
                guess = g
                guess_index = i
                break
        
        if not guess:
            await interaction.response.send_message(
                f"❌ Guess `{guess_id}` not found.",
                ephemeral=True
            )
            return
        
        # Update guess
        guesses[guess_index]['is_correct'] = True
        guesses[guess_index]['actual_amount'] = actual_amount
        guesses[guess_index]['corrected_at'] = datetime.now().isoformat()
        guesses[guess_index]['corrected_by'] = interaction.user.name
        
        # Calculate accuracy
        guessed_amount = guess.get('amount', 0)
        accuracy = 100 - abs((guessed_amount - actual_amount) / actual_amount * 100)
        
        # Save updated guesses
        save_guesses(guesses)
        
        # Create response embed
        embed = discord.Embed(
            title="✅ Guess Marked as Correct",
            description=f"Guess ID: `{guess_id}`",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Guessed Amount", value=f"${guessed_amount:.2f}", inline=True)
        embed.add_field(name="Actual Amount", value=f"${actual_amount:.2f}", inline=True)
        embed.add_field(name="Accuracy", value=f"{accuracy:.1f}%", inline=True)
        
        embed.add_field(name="User", value=guess.get('username', 'Unknown'), inline=True)
        embed.add_field(name="Month", value=guess.get('month', 'Unknown'), inline=True)
        
        if guess.get('category'):
            embed.add_field(name="Category", value=guess['category'], inline=True)
        
        embed.set_footer(text=f"Corrected by {interaction.user.name}")
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function to add this cog to the bot."""
    await bot.add_cog(GuessCog(bot))
