import discord
import datetime
from config import TOP_IMAGE, BOTTOM_IMAGE, TICKET_ROLES, TICKET_CATEGORY_ID
from .views import TicketControls

async def create_ticket(interaction: discord.Interaction, ticket_type: str):
    category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True)
    }
    
    for role_id in TICKET_ROLES[ticket_type]:
        role = interaction.guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True)
    
    timestamp = datetime.datetime.now().strftime('%m%d')
    channel_name = f"{ticket_type.lower().replace(' ', '-')}-{interaction.user.name}-{timestamp}"
    
    channel = await interaction.guild.create_text_channel(
        name=channel_name,
        category=category,
        overwrites=overwrites
    )
    
    embeds = [
        discord.Embed(color=0x2b2d31).set_image(url=TOP_IMAGE),
        discord.Embed(
            title="Support Ticket",
            description=(
                "📩 Ticket Created\n"
                "Thank you for reaching out! Support will be with you shortly.\n\n"
                f"🛠️ Support Type: `{ticket_type}`\n"
                f"👤 Created by: {interaction.user.mention}\n"
                f"📅 Opened at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "# Please do not ping staff - be patient"
            ),
            color=0x2b2d31
        ).set_image(url=BOTTOM_IMAGE)
    ]
    
    await channel.send(
        content=f"{interaction.user.mention} Welcome to your ticket!",
        embeds=embeds,
        view=TicketControls()
    )
    await interaction.response.send_message(
        f"✅ Ticket created: {channel.mention}", 
        ephemeral=True
    )