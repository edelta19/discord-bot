import discord
from discord import app_commands
from discord.ext import commands
from .views import TicketPanelView
from config import TOP_IMAGE, BOTTOM_IMAGE
import json
import os

PANEL_DATA_FILE = "tickets/panel_data.json"

def load_panel_data():
    if os.path.exists(PANEL_DATA_FILE):
        try:
            with open(PANEL_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_panel_data(data):
    with open(PANEL_DATA_FILE, 'w') as f:
        json.dump(data, f)

class TicketPanels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.panel_data = load_panel_data()
        self.restored_panels = False

    async def restore_panels(self):
        """Restore all panels from saved data"""
        if self.restored_panels:
            return
            
        print("♻️ Restoring ticket panels...")
        restored_count = 0
        
        for channel_id, message_id in self.panel_data.items():
            try:
                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    continue
                    
                try:
                    message = await channel.fetch_message(int(message_id))
                    await message.edit(view=TicketPanelView())
                    restored_count += 1
                except discord.NotFound:
                    del self.panel_data[channel_id]
                    save_panel_data(self.panel_data)
            except Exception as e:
                print(f"❌ Error restoring panel in {channel_id}: {e}")
        
        print(f"✅ Restored {restored_count} ticket panels")
        self.restored_panels = True

    @commands.Cog.listener()
    async def on_ready(self):
        await self.restore_panels()

    @app_commands.command(
        name="send-panel",
        description="Send the ticket panel to a channel"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def send_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Sends the ticket panel to the specified channel"""
        embeds = [
            discord.Embed(color=0x2b2d31).set_image(url=TOP_IMAGE),
            discord.Embed(
                title="Server Support",
                description=(
                    "🎟️ Ticket Support Information\n\n"
                    "🔹 **General Support**\n"
                    "> For general questions, concerns, or assistance with server features.\n\n"
                    "🔹 **Management Support**\n"
                    "> Report a member or staff behavior that violates server rules or expectations.\n\n"
                    "🔹 **Leadership Support**\n"
                    "> Use for claiming shop items, reporting raids, or addressing high-rank issues.\n\n"
                    "📌 Please select the appropriate category when opening a ticket so we can assist you faster."
                ),
                color=0x2b2d31
            ).set_image(url=BOTTOM_IMAGE)
        ]
        
        view = TicketPanelView()
        message = await channel.send(embeds=embeds, view=view)
        
        self.panel_data[str(channel.id)] = message.id
        save_panel_data(self.panel_data)
        
        await interaction.response.send_message("✅ Panel sent successfully!", ephemeral=True)