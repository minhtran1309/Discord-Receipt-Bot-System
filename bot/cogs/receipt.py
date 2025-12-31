"""Receipt management cog with slash commands."""
import uuid
from datetime import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from bot.models import Receipt, ReceiptItem
from bot.storage import load_receipts, add_receipt, get_receipt_by_id


class ReceiptCog(commands.Cog):
    """Cog for managing receipts."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    receipt_group = app_commands.Group(
        name="receipt",
        description="Manage receipts"
    )
    
    @receipt_group.command(name="process", description="Process and add a new receipt")
    @app_commands.describe(
        items="Items in format: name:price:quantity, name:price:quantity, ...",
        notes="Optional notes for the receipt"
    )
    async def process_receipt(
        self,
        interaction: discord.Interaction,
        items: str,
        notes: Optional[str] = None
    ):
        """Process and add a new receipt."""
        try:
            # Parse items
            receipt_items = []
            for item_str in items.split(','):
                parts = [p.strip() for p in item_str.strip().split(':')]
                if len(parts) < 2:
                    await interaction.response.send_message(
                        f"❌ Invalid item format: {item_str}. Use: name:price or name:price:quantity",
                        ephemeral=True
                    )
                    return
                
                name = parts[0]
                price = float(parts[1])
                quantity = int(parts[2]) if len(parts) > 2 else 1
                
                receipt_items.append(ReceiptItem(
                    name=name,
                    price=price,
                    quantity=quantity
                ))
            
            # Create receipt
            receipt_id = str(uuid.uuid4())[:8]
            receipt = Receipt(
                id=receipt_id,
                user_id=interaction.user.id,
                username=interaction.user.name,
                items=receipt_items,
                notes=notes
            )
            
            # Save receipt
            add_receipt(receipt.model_dump(mode='json'))
            
            # Create response embed
            embed = discord.Embed(
                title="✅ Receipt Processed",
                description=f"Receipt ID: `{receipt_id}`",
                color=discord.Color.green(),
                timestamp=receipt.timestamp
            )
            
            # Add items to embed
            items_text = "\n".join([
                f"• {item.name}: ${item.price:.2f} x {item.quantity} = ${item.total:.2f}"
                for item in receipt.items
            ])
            embed.add_field(name="Items", value=items_text, inline=False)
            embed.add_field(name="Total", value=f"${receipt.total_amount:.2f}", inline=False)
            
            if notes:
                embed.add_field(name="Notes", value=notes, inline=False)
            
            embed.set_footer(text=f"Submitted by {interaction.user.name}")
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Error parsing receipt: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error processing receipt: {str(e)}",
                ephemeral=True
            )
    
    @receipt_group.command(name="list", description="List all receipts")
    @app_commands.describe(
        user="Filter receipts by user (optional)"
    )
    async def list_receipts(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None
    ):
        """List all receipts, optionally filtered by user."""
        receipts = load_receipts()
        
        if user:
            receipts = [r for r in receipts if r.get('user_id') == user.id]
            title = f"Receipts for {user.name}"
        else:
            title = "All Receipts"
        
        if not receipts:
            await interaction.response.send_message(
                "📭 No receipts found.",
                ephemeral=True
            )
            return
        
        # Sort by timestamp (newest first)
        receipts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Create embed
        embed = discord.Embed(
            title=title,
            color=discord.Color.blue()
        )
        
        # Add receipts to embed (limit to 10 most recent)
        for receipt in receipts[:10]:
            receipt_id = receipt.get('id', 'Unknown')
            username = receipt.get('username', 'Unknown')
            total = receipt.get('total_amount', 0)
            timestamp = receipt.get('timestamp', '')
            
            field_value = f"User: {username}\nTotal: ${total:.2f}\nDate: {timestamp[:10]}"
            embed.add_field(
                name=f"Receipt `{receipt_id}`",
                value=field_value,
                inline=True
            )
        
        if len(receipts) > 10:
            embed.set_footer(text=f"Showing 10 of {len(receipts)} receipts")
        
        await interaction.response.send_message(embed=embed)
    
    @receipt_group.command(name="show", description="Show details of a specific receipt")
    @app_commands.describe(
        receipt_id="The ID of the receipt to show"
    )
    async def show_receipt(
        self,
        interaction: discord.Interaction,
        receipt_id: str
    ):
        """Show detailed information about a specific receipt."""
        receipt = get_receipt_by_id(receipt_id)
        
        if not receipt:
            await interaction.response.send_message(
                f"❌ Receipt `{receipt_id}` not found.",
                ephemeral=True
            )
            return
        
        # Create detailed embed
        embed = discord.Embed(
            title=f"Receipt `{receipt_id}`",
            color=discord.Color.blue()
        )
        
        # Add receipt details
        embed.add_field(
            name="User",
            value=receipt.get('username', 'Unknown'),
            inline=True
        )
        embed.add_field(
            name="Date",
            value=receipt.get('timestamp', 'Unknown')[:10],
            inline=True
        )
        embed.add_field(
            name="Total",
            value=f"${receipt.get('total_amount', 0):.2f}",
            inline=True
        )
        
        # Add items
        items = receipt.get('items', [])
        if items:
            items_list = []
            for item in items:
                name = item.get('name')
                price = item.get('price', 0)
                quantity = item.get('quantity', 1)
                total = price * quantity
                items_list.append(f"• {name}: ${price:.2f} x {quantity} = ${total:.2f}")
            
            items_text = "\n".join(items_list)
            embed.add_field(name="Items", value=items_text, inline=False)
        
        # Add notes if present
        if receipt.get('notes'):
            embed.add_field(name="Notes", value=receipt['notes'], inline=False)
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function to add this cog to the bot."""
    await bot.add_cog(ReceiptCog(bot))
