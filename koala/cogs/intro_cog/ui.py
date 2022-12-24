import discord
from discord import ui

from . import core
from .utils import BASE_LEGAL_MESSAGE


class EditWelcomeMessage(ui.Modal, title='Edit Welcome Message'):
    message = ui.TextInput(label='Welcome Message', style=discord.TextStyle.paragraph, max_length=1500)

    def __init__(self, default):
        super().__init__()
        self.message.default = default

    async def on_submit(self, interaction: discord.Interaction):
        new_message = self.message.value.lstrip()
        core.update_guild_welcome_message(interaction.guild_id, new_message)
        await interaction.response.send_message(f'Thanks for your response we have updated the welcome message to:'
                                                f'\n\r{new_message}\n\r{BASE_LEGAL_MESSAGE}', ephemeral=True)
