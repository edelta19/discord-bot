import discord
from discord import app_commands
from discord.ext import commands
from config import MOD_ROLES, ADMIN_ROLES, MOD_LOG_CHANNEL
import datetime

class TimeoutCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="timeout", description="Timeout a user")
    @app_commands.checks.has_any_role(*MOD_ROLES, *ADMIN_ROLES)
    async def timeout_command(self, interaction: discord.Interaction, 
                             user: discord.Member, 
                             duration_minutes: int, 
                             reason: str):
        """Timeout a user for a specified duration"""
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot timeout yourself!", ephemeral=True)
        
        if any(role.id in ADMIN_ROLES for role in user.roles):
            return await interaction.response.send_message("❌ You cannot timeout an admin!", ephemeral=True)
        
        try:
            duration = datetime.timedelta(minutes=duration_minutes)
            
            await user.timeout(duration, reason=f"{interaction.user.name}: {reason}")
            
            await interaction.response.send_message(
                f"⏳ {user.mention} has been timed out for {duration_minutes} minutes for: {reason}",
                ephemeral=True
            )
            
            log_channel = self.bot.get_channel(MOD_LOG_CHANNEL)
            if log_channel:
                embed = discord.Embed(
                    title="⏰ User Timed Out",
                    color=discord.Color.gold(),
                    timestamp=datetime.datetime.now()
                )
                embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                embed.add_field(name="Duration", value=f"{duration_minutes} minutes", inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.set_footer(text=f"ID: {user.id}")
                await log_channel.send(embed=embed)
                
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to timeout this user!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TimeoutCog(bot))