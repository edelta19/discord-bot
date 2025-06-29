import discord
from discord import app_commands
from discord.ext import commands
from config import ADMIN_ROLES, MOD_LOG_CHANNEL
import datetime

class BanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.checks.has_any_role(*ADMIN_ROLES)
    async def ban_command(self, interaction: discord.Interaction, 
                         user: discord.Member, 
                         reason: str, 
                         delete_days: app_commands.Range[int, 0, 7] = 0):
        """Ban a user with optional message deletion"""
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot ban yourself!", ephemeral=True)
        
        if any(role.id in ADMIN_ROLES for role in user.roles):
            return await interaction.response.send_message("❌ You cannot ban an admin!", ephemeral=True)
        
        try:
            try:
                await user.send(f"You've been banned from **{interaction.guild.name}** for: {reason}")
            except discord.Forbidden:
                pass
            
            await user.ban(reason=f"{interaction.user.name}: {reason}", delete_message_days=delete_days)
            
            await interaction.response.send_message(f"✅ {user.mention} has been banned for: {reason}", ephemeral=True)
            
            log_channel = self.bot.get_channel(MOD_LOG_CHANNEL)
            if log_channel:
                embed = discord.Embed(
                    title="🔨 User Banned",
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.now()
                )
                embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Messages Deleted", value=f"{delete_days} days", inline=False)
                embed.set_footer(text=f"ID: {user.id}")
                await log_channel.send(embed=embed)
                
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to ban this user!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BanCog(bot))