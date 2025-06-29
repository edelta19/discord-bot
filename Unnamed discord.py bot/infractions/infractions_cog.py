import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import datetime
import uuid
from config import INTERNAL_AFFAIRS_ROLES, INFRACTIONS_LOG_CHANNEL

# File to store infractions data
DATA_FILE = "infractions/infractions_data.json"

def load_infractions_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_infractions_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

class InfractionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.infractions_data = load_infractions_data()
        
    def has_permission(self, user: discord.Member):
        """Check if user has internal affairs role"""
        return any(role.id in INTERNAL_AFFAIRS_ROLES for role in user.roles)
    
    def create_infraction_embed(self, user, moderator, punishment, reason, infraction_id):
        embed = discord.Embed(
            title="📝 STAFF INFRACTION",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="👤 Staff Member", value=f"{user.mention} ({user.id})", inline=False)
        embed.add_field(name="🛠️ Moderator", value=moderator.mention, inline=False)
        embed.add_field(name="⚖️ Punishment", value=punishment, inline=False)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.add_field(name="🆔 Infraction ID", value=f"`{infraction_id}`", inline=False)
        embed.set_footer(text="Internal Affairs Division")
        return embed

    @app_commands.command(name="infract", description="Issue an infraction to a staff member")
    async def infract_command(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        punishment: str,
        reason: str
    ):
        """Issue an infraction to a staff member"""
        # Check permissions
        if not self.has_permission(interaction.user):
            return await interaction.response.send_message(
                "❌ You don't have permission to issue infractions!",
                ephemeral=True
            )
            
        # Prevent self-infraction
        if user.id == interaction.user.id:
            return await interaction.response.send_message(
                "❌ You cannot issue an infraction to yourself!",
                ephemeral=True
            )
            
        # Generate unique ID
        infraction_id = str(uuid.uuid4())[:8].upper()
        
        # Get current timestamp
        timestamp = datetime.datetime.now().isoformat()
        
        # Create infraction record
        infraction = {
            "id": infraction_id,
            "user_id": user.id,
            "moderator_id": interaction.user.id,
            "punishment": punishment,
            "reason": reason,
            "timestamp": timestamp
        }
        
        # Save to data
        guild_id = str(interaction.guild.id)
        if guild_id not in self.infractions_data:
            self.infractions_data[guild_id] = {}
            
        if str(user.id) not in self.infractions_data[guild_id]:
            self.infractions_data[guild_id][str(user.id)] = []
            
        self.infractions_data[guild_id][str(user.id)].append(infraction)
        save_infractions_data(self.infractions_data)
        
        # Send confirmation
        await interaction.response.send_message(
            f"✅ Infraction issued to {user.mention} (ID: `{infraction_id}`)",
            ephemeral=True
        )
        
        # Log to infractions channel
        log_channel = self.bot.get_channel(INFRACTIONS_LOG_CHANNEL)
        if log_channel:
            embed = self.create_infraction_embed(user, interaction.user, punishment, reason, infraction_id)
            await log_channel.send(embed=embed)
            
        # DM the staff member
        try:
            dm_embed = discord.Embed(
                title="⚠️ STAFF INFRACTION NOTICE",
                description=f"You have received a staff infraction in **{interaction.guild.name}**",
                color=discord.Color.dark_red()
            )
            dm_embed.add_field(name="Punishment", value=punishment, inline=False)
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.add_field(name="Infraction ID", value=f"`{infraction_id}`", inline=False)
            dm_embed.add_field(name="Issued By", value=interaction.user.mention, inline=False)
            dm_embed.set_footer(text="Contact Internal Affairs for more information")
            
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled

async def setup(bot):
    await bot.add_cog(InfractionsCog(bot))