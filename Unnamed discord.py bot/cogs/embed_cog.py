import discord
from discord import app_commands
from discord.ui import Modal, TextInput
from discord.ext import commands

class EmbedModal(Modal, title="Create Custom Embed"):
    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {}

        self.input_title = TextInput(
            label="Title (Title | Hex Color)",
            placeholder="Example: Important Update | #FF0000",
            required=False,
            max_length=256
        )

        self.input_body = TextInput(
            label="Body Content",
            placeholder="Main content here...",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=4000
        )

        self.input_thumbnail = TextInput(
            label="Thumbnail (Top Right Image)",
            placeholder="URL for small top-right image...",
            required=False
        )

        self.input_top_main_image = TextInput(
            label="Top + Main Image (separate by |)",
            placeholder="https://top.png | https://main.png",
            required=False
        )

        self.input_metadata = TextInput(
            label="Author & Footer",
            placeholder="Author | Author Icon | Footer | Footer Icon",
            required=False
        )

        self.add_item(self.input_title)
        self.add_item(self.input_body)
        self.add_item(self.input_thumbnail)
        self.add_item(self.input_top_main_image)
        self.add_item(self.input_metadata)

    async def on_submit(self, interaction: discord.Interaction):
        # === Parse title & color ===
        title = ''
        color = None
        if self.input_title.value:
            parts = [p.strip() for p in self.input_title.value.split('|')]
            title = parts[0] if len(parts) > 0 else ''
            if len(parts) > 1:
                try:
                    color = discord.Color.from_str(parts[1])
                except:
                    await interaction.response.send_message("❌ Invalid color format! Use hex like #FF0000", ephemeral=True)
                    return

        # === Parse top + main image ===
        top_image_url = ''
        main_image_url = ''
        if self.input_top_main_image.value:
            parts = [p.strip() for p in self.input_top_main_image.value.split('|')]
            top_image_url = parts[0] if len(parts) > 0 else ''
            main_image_url = parts[1] if len(parts) > 1 else ''

        # Save user input
        user_data = {
            'title': self.input_title.value,
            'body': self.input_body.value,
            'thumbnail': self.input_thumbnail.value,
            'top_image': top_image_url,
            'main_image': main_image_url,
            'metadata': self.input_metadata.value
        }

        cog = interaction.client.get_cog("EmbedCog")
        if cog:
            cog.user_data[interaction.user.id] = user_data

        # Validate image URLs
        if top_image_url and not top_image_url.startswith(('http://', 'https://')):
            await interaction.response.send_message("❌ Invalid top image URL!", ephemeral=True)
            return
        if main_image_url and not main_image_url.startswith(('http://', 'https://')):
            await interaction.response.send_message("❌ Invalid main image URL!", ephemeral=True)
            return

        embeds = []

        # === First Embed: Top Image ===
        if top_image_url:
            top_embed = discord.Embed(color=color or discord.Color.default())
            top_embed.set_image(url=top_image_url)
            embeds.append(top_embed)

        # === Second Embed: Main Content ===
        embed = discord.Embed(color=color or discord.Color.default())

        if title:
            embed.title = title
        if self.input_body.value:
            embed.description = self.input_body.value
        if self.input_thumbnail.value and self.input_thumbnail.value.startswith(('http://', 'https://')):
            embed.set_thumbnail(url=self.input_thumbnail.value)
        elif self.input_thumbnail.value:
            await interaction.response.send_message("❌ Invalid thumbnail URL!", ephemeral=True)
            return
        if main_image_url:
            embed.set_image(url=main_image_url)

        # === Metadata ===
        if self.input_metadata.value:
            parts = [p.strip() for p in self.input_metadata.value.split('|') if p.strip()]
            if len(parts) > 0:
                author_name = parts[0]
                author_icon = parts[1] if len(parts) > 1 else None
                if author_icon and not author_icon.startswith(('http://', 'https://')):
                    author_icon = None
                embed.set_author(name=author_name, icon_url=author_icon)

            if len(parts) > 2:
                footer_text = parts[2]
                footer_icon = parts[3] if len(parts) > 3 else None
                if footer_icon and not footer_icon.startswith(('http://', 'https://')):
                    footer_icon = None
                embed.set_footer(text=footer_text, icon_url=footer_icon)

        embeds.append(embed)
        await interaction.response.send_message(embeds=embeds)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('❌ An error occurred!', ephemeral=True)
        print(f"Modal error: {error}")

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}

    @app_commands.command(name="embed", description="Create a custom embed with a form")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def embed_command(self, interaction: discord.Interaction):
        user_data = self.user_data.get(interaction.user.id, {})
        modal = EmbedModal(user_data)

        modal.input_title.default = user_data.get('title', '')
        modal.input_body.default = user_data.get('body', '')
        modal.input_thumbnail.default = user_data.get('thumbnail', '')
        modal.input_top_main_image.default = f"{user_data.get('top_image', '')} | {user_data.get('main_image', '')}"
        modal.input_metadata.default = user_data.get('metadata', '')

        await interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(EmbedCog(bot))
