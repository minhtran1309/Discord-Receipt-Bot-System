"""Clerk management cog with slash commands for syncing and reporting."""
from datetime import datetime
from typing import Optional
from collections import defaultdict

import discord
from discord import app_commands
from discord.ext import commands

from bot.storage import load_receipts, load_guesses


class ClerkCog(commands.Cog):
    """Cog for clerk/admin management commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    clerk_group = app_commands.Group(
        name="clerk",
        description="Clerk and admin commands"
    )
    
    @clerk_group.command(name="sync", description="Sync slash commands with Discord")
    async def sync_commands(self, interaction: discord.Interaction):
        """Sync slash commands with Discord."""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Sync commands to the guild
            synced = await self.bot.tree.sync(guild=interaction.guild)
            
            await interaction.followup.send(
                f"✅ Synced {len(synced)} commands to the current guild.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error syncing commands: {str(e)}",
                ephemeral=True
            )
    
    @clerk_group.command(name="spent", description="Calculate total spending")
    @app_commands.describe(
        user="Filter by user (optional)",
        start_date="Start date in YYYY-MM-DD format (optional)",
        end_date="End date in YYYY-MM-DD format (optional)"
    )
    async def calculate_spent(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """Calculate total spending from receipts."""
        receipts = load_receipts()
        
        # Filter by user if specified
        if user:
            receipts = [r for r in receipts if r.get('user_id') == user.id]
        
        # Filter by date range if specified
        if start_date:
            try:
                start = datetime.fromisoformat(start_date)
                receipts = [r for r in receipts if datetime.fromisoformat(r.get('timestamp', '')) >= start]
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid start_date format. Use YYYY-MM-DD",
                    ephemeral=True
                )
                return
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date)
                receipts = [r for r in receipts if datetime.fromisoformat(r.get('timestamp', '')) <= end]
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid end_date format. Use YYYY-MM-DD",
                    ephemeral=True
                )
                return
        
        if not receipts:
            await interaction.response.send_message(
                "📭 No receipts found for the specified criteria.",
                ephemeral=True
            )
            return
        
        # Calculate total
        total_spent = sum(r.get('total_amount', 0) for r in receipts)
        
        # Calculate per-user breakdown
        user_totals = defaultdict(float)
        for receipt in receipts:
            username = receipt.get('username', 'Unknown')
            user_totals[username] += receipt.get('total_amount', 0)
        
        # Create embed
        embed = discord.Embed(
            title="💰 Spending Report",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Total Spent",
            value=f"${total_spent:.2f}",
            inline=False
        )
        
        embed.add_field(
            name="Number of Receipts",
            value=str(len(receipts)),
            inline=True
        )
        
        # Add filters info
        filters = []
        if user:
            filters.append(f"User: {user.name}")
        if start_date:
            filters.append(f"From: {start_date}")
        if end_date:
            filters.append(f"To: {end_date}")
        
        if filters:
            embed.add_field(
                name="Filters",
                value="\n".join(filters),
                inline=False
            )
        
        # Add per-user breakdown if not filtered by user
        if not user and len(user_totals) > 0:
            breakdown = "\n".join([
                f"• {username}: ${amount:.2f}"
                for username, amount in sorted(user_totals.items(), key=lambda x: x[1], reverse=True)
            ])
            embed.add_field(
                name="Per User Breakdown",
                value=breakdown,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @clerk_group.command(name="monthly", description="Get monthly spending report")
    @app_commands.describe(
        month="Month in YYYY-MM format (optional, defaults to current month)"
    )
    async def monthly_report(
        self,
        interaction: discord.Interaction,
        month: Optional[str] = None
    ):
        """Generate a monthly spending report."""
        # Use current month if not provided
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        # Validate month format
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid month format. Use YYYY-MM",
                ephemeral=True
            )
            return
        
        # Load receipts and filter by month
        receipts = load_receipts()
        monthly_receipts = [
            r for r in receipts
            if r.get('timestamp', '')[:7] == month
        ]
        
        # Load guesses and filter by month
        guesses = load_guesses()
        monthly_guesses = [
            g for g in guesses
            if g.get('month') == month
        ]
        
        # Create embed
        embed = discord.Embed(
            title=f"📊 Monthly Report - {month}",
            color=discord.Color.purple()
        )
        
        # Receipts section
        if monthly_receipts:
            total_spent = sum(r.get('total_amount', 0) for r in monthly_receipts)
            embed.add_field(
                name="📄 Receipts",
                value=f"Count: {len(monthly_receipts)}\nTotal: ${total_spent:.2f}",
                inline=True
            )
            
            # Per-user breakdown
            user_totals = defaultdict(float)
            for receipt in monthly_receipts:
                username = receipt.get('username', 'Unknown')
                user_totals[username] += receipt.get('total_amount', 0)
            
            breakdown = "\n".join([
                f"• {username}: ${amount:.2f}"
                for username, amount in sorted(user_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            ])
            embed.add_field(
                name="Top Spenders",
                value=breakdown or "No data",
                inline=False
            )
        else:
            embed.add_field(
                name="📄 Receipts",
                value="No receipts found",
                inline=True
            )
        
        # Guesses section
        if monthly_guesses:
            total_guesses = len(monthly_guesses)
            correct_guesses = len([g for g in monthly_guesses if g.get('is_correct')])
            
            embed.add_field(
                name="🎯 Guesses",
                value=f"Total: {total_guesses}\nCorrect: {correct_guesses}",
                inline=True
            )
            
            # Show best guess if any are correct
            correct = [g for g in monthly_guesses if g.get('is_correct')]
            if correct:
                best = min(correct, key=lambda g: abs(g.get('amount', 0) - g.get('actual_amount', 0)))
                accuracy = 100 - abs((best.get('amount', 0) - best.get('actual_amount', 0)) / best.get('actual_amount', 1) * 100)
                
                embed.add_field(
                    name="Best Guess",
                    value=f"{best.get('username')}: ${best.get('amount', 0):.2f} ({accuracy:.1f}% accurate)",
                    inline=False
                )
        else:
            embed.add_field(
                name="🎯 Guesses",
                value="No guesses found",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function to add this cog to the bot."""
    await bot.add_cog(ClerkCog(bot))
