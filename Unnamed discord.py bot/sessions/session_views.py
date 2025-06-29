import discord
from discord.ui import Button, View

class SessionVoteView(View):
    def __init__(self, cog, required_votes, channel_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.required_votes = required_votes
        self.channel_id = channel_id
        
    @discord.ui.button(
        label="Vote to Start", 
        style=discord.ButtonStyle.green,
        emoji="✅",
        custom_id="session_vote_button"
    )
    async def vote_button(self, interaction: discord.Interaction, button: Button):
        await self.cog.handle_vote(interaction, str(interaction.message.id))