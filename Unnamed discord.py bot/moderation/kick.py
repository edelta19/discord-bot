import discord
from discord import app_commands
from discord.ext import commands
from config import MOD_ROLES, ADMIN_ROLES, MOD_LOG_CHANNEL
import datetime

class KickCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.checks.has_any_role(*MOD_ROLES, *ADMIN_ROLES)
    async def kick_command(self, interaction: discord.Interaction, 
                          user: discord.Member, 
                          reason: str):
        """Kick a user from the server"""
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot kick yourself!", ephemeral=True)
        
        if any(role.id in ADMIN_ROLES for role in user.roles):
            return await interaction.response.send_message("❌ You cannot kick an admin!", ephemeral=True)
        
        try:
            try:
                await user.send(f"You've been kicked from **{interaction.guild.name}** for: {reason}")
            except discord.Forbidden:
                pass
            
            await user.kick(reason=f"{interaction.user.name}: {reason}")
            
            await interaction.response.send_message(f"{user.mention} has been kicked for: {reason}", ephemeral=True)
            
            log_channel = self.bot.get_channel(MOD_LOG_CHANNEL)
            if log_channel:
                embed = discord.Embed(
                    title="User Kicked",
                    color=discord.Color.orange(),
                    timestamp=datetime.datetime.now()
                )
                embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.set_footer(text=f"ID: {user.id}")
                await log_channel.send(embed=embed)
                
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to kick this user!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(KickCog(bot))