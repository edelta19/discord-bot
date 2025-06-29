import discord
from discord import app_commands
from discord.ext import commands
from config import MOD_ROLES, ADMIN_ROLES, MOD_LOG_CHANNEL
import datetime

class WarnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}  # {guild_id: {user_id: [warnings]}}

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.checks.has_any_role(*MOD_ROLES, *ADMIN_ROLES)
    async def warn_command(self, interaction: discord.Interaction, 
                          user: discord.Member, 
                          reason: str):
        """Warn a user and log the warning"""
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot warn yourself!", ephemeral=True)
        
        guild_id = interaction.guild.id
        user_id = user.id
        
        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
        if user_id not in self.warnings[guild_id]:
            self.warnings[guild_id][user_id] = []
            
        warning = {
            "moderator": interaction.user.id,
            "reason": reason,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.warnings[guild_id][user_id].append(warning)
        
        await interaction.response.send_message(f"⚠️ {user.mention} has been warned for: {reason}", ephemeral=True)
        
        try:
            await user.send(f"You've been warned in **{interaction.guild.name}** for: {reason}")
        except discord.Forbidden:
            pass
        
        log_channel = self.bot.get_channel(MOD_LOG_CHANNEL)
        if log_channel:
            embed = discord.Embed(
                title="⚠️ User Warned",
                color=discord.Color.yellow(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Total Warnings", value=str(len(self.warnings[guild_id][user_id])), inline=False)
            embed.set_footer(text=f"ID: {user.id}")
            await log_channel.send(embed=embed)

    @app_commands.command(name="warnings", description="View a user's warnings")
    @app_commands.checks.has_any_role(*MOD_ROLES, *ADMIN_ROLES)
    async def warnings_command(self, interaction: discord.Interaction, user: discord.Member):
        """View a user's warnings"""
        guild_id = interaction.guild.id
        user_id = user.id
        
        if guild_id in self.warnings and user_id in self.warnings[guild_id]:
            warnings = self.warnings[guild_id][user_id]
            warning_list = "\n".join(
                f"{i+1}. {w['reason']} - <@{w['moderator']}> ({w['timestamp'].split('T')[0]})"
                for i, w in enumerate(warnings))
            
            embed = discord.Embed(
                title=f"⚠️ Warnings for {user.display_name}",
                description=warning_list,
                color=discord.Color.yellow()
            )
            embed.set_footer(text=f"Total warnings: {len(warnings)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"ℹ️ {user.mention} has no warnings.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WarnCog(bot))