import discord
from discord import app_commands
from discord.ext import commands
from tickets.panels import TicketPanels
from tickets.views import TicketPanelView, TicketControls
from sessions.session_cog import SessionCog
from sessions.session_views import SessionVoteView
from infractions.infractions_cog import InfractionsCog
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # Load cogs
    await load_cogs()
    
    # Register persistent views
    bot.add_view(TicketPanelView())
    bot.add_view(TicketControls())
    bot.add_view(SessionVoteView(None, 0, 0))  # Register vote button view
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")
    
    print(f"✅ Bot ready as {bot.user}")
    print(f"🔗 Invite URL: https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands")

async def load_cogs():
    """Load all cogs"""
    # Load ticket system
    await bot.add_cog(TicketPanels(bot))
    
    # Load embed cog
    try:
        await bot.load_extension("cogs.embed_cog")
        print("✅ Loaded embed_cog")
    except commands.ExtensionNotFound:
        print("❌ embed_cog not found in cogs directory")
    except commands.ExtensionFailed as e:
        print(f"❌ Failed to load embed_cog: {e}")
    
    # Load moderation cogs
    mod_cogs = ["ban", "kick", "timeout", "warn"]
    for cog in mod_cogs:
        try:
            await bot.load_extension(f"moderation.{cog}")
            print(f"✅ Loaded moderation cog: {cog}")
        except commands.ExtensionNotFound:
            print(f"❌ moderation.{cog} not found")
        except commands.ExtensionFailed as e:
            print(f"❌ Failed to load moderation.{cog}: {e}")
    
    # Load session cog
    try:
        await bot.add_cog(SessionCog(bot))
        print("✅ Loaded session_cog")
    except Exception as e:
        print(f"❌ Failed to load session_cog: {e}")
    
    # Load infractions cog
    try:
        await bot.add_cog(InfractionsCog(bot))
        print("✅ Loaded infractions_cog")
    except Exception as e:
        print(f"❌ Failed to load infractions_cog: {e}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("🚫 You don't have permission to do that!", ephemeral=True)
    elif isinstance(error, app_commands.MissingAnyRole):
        await interaction.response.send_message("🚫 You don't have the required role for this command!", ephemeral=True)
    elif isinstance(error, app_commands.CommandInvokeError):
        await interaction.response.send_message(f"⚠️ An error occurred: {str(error.original)}", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Error: {str(error)}", ephemeral=True)

if __name__ == "__main__":
    bot.run('discord bot token goes here')