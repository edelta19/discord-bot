import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import asyncio
import time
from datetime import datetime
from config import MANAGEMENT_ROLES, SESSION_IMAGE, SESSION_COOLDOWN
from .session_views import SessionVoteView

# File to store session data
DATA_FILE = "sessions/session_data.json"

def load_session_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_session_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def create_session_embed(title, description):
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.set_image(url=SESSION_IMAGE)
    return embed

class SessionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session_data = load_session_data()
        self.active_votes = {}
        self.last_command = {}  # {user_id: last_command_time}
        
    def has_permission(self, user: discord.Member):
        """Check if user has management role"""
        return any(role.id in MANAGEMENT_ROLES for role in user.roles)
    
    def check_cooldown(self, user_id: int):
        """Check if user is on cooldown"""
        current_time = time.time()
        if user_id in self.last_command:
            if current_time - self.last_command[user_id] < SESSION_COOLDOWN:
                return False
        self.last_command[user_id] = current_time
        return True

    @app_commands.command(name="session-start", description="Start a new session")
    async def session_start(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Start a new session in the specified channel"""
        # Check permissions
        if not self.has_permission(interaction.user):
            return await interaction.response.send_message(
                "❌ You don't have permission to manage sessions!",
                ephemeral=True
            )
            
        # Check cooldown
        if not self.check_cooldown(interaction.user.id):
            return await interaction.response.send_message(
                f"❌ Please wait {SESSION_COOLDOWN} seconds between session commands!",
                ephemeral=True
            )
        
        embed = create_session_embed(
            "🟢 SESSION STARTED", 
            "The server is now up! You can join the game and start roleplaying."
        )
        
        try:
            message = await channel.send(content="@everyone", embed=embed)
            
            # Save session data
            self.session_data[str(interaction.guild.id)] = {
                "message_id": message.id,
                "channel_id": channel.id,
                "active": True
            }
            save_session_data(self.session_data)
            
            await interaction.response.send_message(
                f"✅ Session started in {channel.mention}", 
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to send messages in that channel!",
                ephemeral=True
            )

    @app_commands.command(name="session-end", description="End the current session")
    async def session_end(self, interaction: discord.Interaction):
        """End the current session"""
        # Check permissions
        if not self.has_permission(interaction.user):
            return await interaction.response.send_message(
                "❌ You don't have permission to manage sessions!",
                ephemeral=True
            )
            
        # Check cooldown
        if not self.check_cooldown(interaction.user.id):
            return await interaction.response.send_message(
                f"❌ Please wait {SESSION_COOLDOWN} seconds between session commands!",
                ephemeral=True
            )
        
        guild_id = str(interaction.guild.id)
        if guild_id not in self.session_data or not self.session_data[guild_id]["active"]:
            return await interaction.response.send_message(
                "❌ No active session to end!",
                ephemeral=True
            )
        
        data = self.session_data[guild_id]
        try:
            channel = self.bot.get_channel(data["channel_id"])
            if not channel:
                raise ValueError("Channel not found")
                
            message = await channel.fetch_message(data["message_id"])
            
            embed = create_session_embed(
                "🔴 SESSION ENDED", 
                "The session has now concluded. Thanks for participating!"
            )
            
            await message.edit(content="Session ended", embed=embed)
            
            # Update session data
            self.session_data[guild_id]["active"] = False
            save_session_data(self.session_data)
            
            await interaction.response.send_message(
                "✅ Session ended successfully!",
                ephemeral=True
            )
        except (discord.NotFound, discord.Forbidden, ValueError) as e:
            await interaction.response.send_message(
                f"❌ Error ending session: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="session-vote", description="Start a session vote")
    async def session_vote(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel,
        required_votes: int
    ):
        """Start a vote to begin a session"""
        # Check permissions
        if not self.has_permission(interaction.user):
            return await interaction.response.send_message(
                "❌ You don't have permission to manage sessions!",
                ephemeral=True
            )
            
        # Check cooldown
        if not self.check_cooldown(interaction.user.id):
            return await interaction.response.send_message(
                f"❌ Please wait {SESSION_COOLDOWN} seconds between session commands!",
                ephemeral=True
            )
        
        if required_votes < 1:
            return await interaction.response.send_message(
                "❌ Required votes must be at least 1!",
                ephemeral=True
            )
            
        embed = create_session_embed(
            "📢 SESSION VOTE", 
            f"Vote to start a new session!\n\n"
            f"✅ 0/{required_votes} votes collected\n\n"
            "Click the button below to vote!"
        )
        
        view = SessionVoteView(self, required_votes, channel.id)
        try:
            message = await channel.send(content="@everyone", embed=embed, view=view)
            
            # Store vote data
            if str(interaction.guild.id) not in self.active_votes:
                self.active_votes[str(interaction.guild.id)] = {}
                
            self.active_votes[str(interaction.guild.id)][str(message.id)] = {
                "required": required_votes,
                "votes": 0,
                "voters": [],
                "channel_id": channel.id
            }
            
            await interaction.response.send_message(
                f"✅ Vote started in {channel.mention}", 
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to send messages in that channel!",
                ephemeral=True
            )

    async def handle_vote(self, interaction: discord.Interaction, message_id: str):
        """Process a vote from the button"""
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        # Get vote data
        if guild_id not in self.active_votes or message_id not in self.active_votes[guild_id]:
            return await interaction.response.send_message(
                "❌ This vote session is no longer active!",
                ephemeral=True
            )
            
        vote_data = self.active_votes[guild_id][message_id]
        
        # Check if user already voted
        if user_id in vote_data["voters"]:
            return await interaction.response.send_message(
                "❌ You've already voted!",
                ephemeral=True
            )
            
        # Add vote
        vote_data["voters"].append(user_id)
        vote_data["votes"] += 1
        
        # Update embed
        votes = vote_data["votes"]
        required = vote_data["required"]
        new_embed = create_session_embed(
            "📢 SESSION VOTE", 
            f"Vote to start a new session!\n\n"
            f"✅ {votes}/{required} votes collected\n\n"
            "Click the button below to vote!"
        )
        
        try:
            channel = self.bot.get_channel(vote_data["channel_id"])
            message = await channel.fetch_message(int(message_id))
            await message.edit(embed=new_embed)
            
            await interaction.response.send_message(
                f"✅ Vote recorded! ({votes}/{required})",
                ephemeral=True
            )
            
            # Check if vote requirement met
            if votes >= required:
                # Start session
                await self.start_session_from_vote(interaction.guild, channel)
                
                # Disable vote button
                for item in message.components:
                    for button in item.children:
                        button.disabled = True
                
                await message.edit(view=None)
                del self.active_votes[guild_id][message_id]
        except discord.NotFound:
            del self.active_votes[guild_id][message_id]
            await interaction.response.send_message(
                "❌ Vote message not found!",
                ephemeral=True
            )

    async def start_session_from_vote(self, guild, channel):
        """Start a session after successful vote"""
        embed = create_session_embed(
            "🟢 SESSION STARTED", 
            "The server is now up! You can join the game and start roleplaying.\n\n"
            "✅ Vote passed successfully!"
        )
        
        try:
            message = await channel.send(content="@everyone", embed=embed)
            
            # Save session data
            self.session_data[str(guild.id)] = {
                "message_id": message.id,
                "channel_id": channel.id,
                "active": True
            }
            save_session_data(self.session_data)
        except discord.Forbidden:
            print(f"Failed to start session in {guild.name}")

async def setup(bot):
    await bot.add_cog(SessionCog(bot))