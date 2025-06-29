import discord
import asyncio
from discord.ui import Select, View, Button

class TicketTypeSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", emoji="🎟️"),
            discord.SelectOption(label="Management Support", emoji="🛡️"),
            discord.SelectOption(label="Leadership Support", emoji="👑")
        ]
        super().__init__(
            placeholder="Select ticket type...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_type_select"
        )

    async def callback(self, interaction: discord.Interaction):
        from .tickets import create_ticket
        await create_ticket(interaction, self.values[0])

class TicketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())

class ClaimButton(Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Claim", custom_id="claim_ticket")

    async def callback(self, interaction: discord.Interaction):
        self.view.add_item(UnclaimButton())
        self.view.remove_item(self)
        await interaction.response.edit_message(view=self.view)
        await interaction.followup.send(f"✅ Ticket claimed by {interaction.user.mention}", ephemeral=True)

class UnclaimButton(Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="Unclaim", custom_id="unclaim_ticket")

    async def callback(self, interaction: discord.Interaction):
        self.view.add_item(ClaimButton())
        self.view.remove_item(self)
        await interaction.response.edit_message(view=self.view)
        await interaction.followup.send("❌ Ticket unclaimed", ephemeral=True)

class CloseButton(Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="Close", custom_id="close_ticket")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Closing ticket in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketControls(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ClaimButton())
        self.add_item(CloseButton())