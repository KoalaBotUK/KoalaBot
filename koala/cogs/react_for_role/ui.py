import enum
from typing import List, Any

import discord
import emoji
from discord import ui, Interaction
from discord._types import ClientT

from koalabot import KOALA_GREEN
from . import core
from .dto import ReactRole


# guild_id: int, channel_id: int, title: str, description: str,
#                              colour: discord.Colour, thumbnail: str = None, inline: bool = None,
#                              roles: List[Tuple[Union[discord.Emoji, str], discord.Role]] = None


class ReactForRoleCreate(ui.Modal, title='Create ReactForRoleMessage'):
    title_text = ui.TextInput(label='Title', style=discord.TextStyle.short)
    description_text = ui.TextInput(label='Description', style=discord.TextStyle.short)
    colour = ui.TextInput(label="Colour", style=discord.TextStyle.short, placeholder="#fff000", required=False,
                          max_length=7)
    thumbnail_url = ui.TextInput(label="Thumbnail URL", style=discord.TextStyle.short, required=False)

    def __init__(self, bot, channel: discord.TextChannel, default_title=None, default_description=None,
                 default_colour=None, default_thumbnail_url=None, message_id=None):
        super().__init__()
        self.bot = bot
        self.channel = channel
        self.title_text.default = default_title
        self.description_text.default = default_description
        self.colour.default = default_colour
        self.thumbnail_url.default = default_thumbnail_url
        self.message_id = message_id

    async def on_submit(self, interaction: discord.Interaction):
        if self.colour.value:
            dis_colour = discord.Colour.from_str(self.colour.value)
        else:
            dis_colour = KOALA_GREEN

        if self.message_id:
            rfr_msg = await core.update_rfr_message(self.bot, self.message_id, interaction.guild_id, self.channel.id,
                                                    self.title_text.value,
                                                    self.description_text.value, dis_colour,
                                                    self.thumbnail_url.value)
            await interaction.response.send_message(f"Your react for role message ID is {rfr_msg.message_id}, "
                                                    f"in {self.channel.mention}. \n"
                                                    f"Applied changes.", ephemeral=True)
        else:
            rfr_msg = await core.create_rfr_message(self.bot, interaction.guild_id, self.channel.id,
                                                    self.title_text.value,
                                                    self.description_text.value, dis_colour,
                                                    self.thumbnail_url.value)

            await interaction.response.send_message(f"Your react for role message ID is {rfr_msg.message_id}, "
                                                    f"in {self.channel.mention}. \n"
                                                    f"Please use `/rfr edit` to add role options", ephemeral=True)


class RfrEditMenuOptions(enum.Enum):
    ALTER_CONFIG = 0
    ADD_ROLES = 1
    REMOVE_ROLES = 2


class RfrEditMenu(discord.ui.View):
    def __init__(self, initial_interaction):
        super().__init__()
        self.value = None
        self.initial_interaction = initial_interaction
        self.interaction = None

    @discord.ui.button(label='Alter Config', style=discord.ButtonStyle.grey)
    async def alter_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = RfrEditMenuOptions.ALTER_CONFIG
        self.alter_config.style = discord.ButtonStyle.green
        self.disable_buttons()
        self.interaction = interaction
        # self.initial_interaction.edit_original_message(view=self)
        self.stop()

    @discord.ui.button(label='Add Roles', style=discord.ButtonStyle.grey)
    async def add_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = RfrEditMenuOptions.ADD_ROLES
        self.add_roles.style = discord.ButtonStyle.green
        self.disable_buttons()
        self.interaction = interaction
        # self.initial_interaction.edit_original_message(view=self)
        self.stop()

    @discord.ui.button(label='Remove Roles', style=discord.ButtonStyle.grey)
    async def remove_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = RfrEditMenuOptions.REMOVE_ROLES
        self.remove_roles.style = discord.ButtonStyle.green
        self.disable_buttons()
        self.interaction = interaction
        # self.initial_interaction.edit_original_message(view=self)
        self.stop()

    def disable_buttons(self):
        self.alter_config.disabled = True
        self.add_roles.disabled = True
        self.remove_roles.disabled = True


class RfrRemoveRoles(discord.ui.View):
    class RfrSelect(discord.ui.Select):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        async def callback(self, interaction: Interaction[ClientT]) -> Any:
            await interaction.response.defer()

    def __init__(self, guild: discord.Guild, react_roles: List[ReactRole]):
        super().__init__()
        options = [discord.SelectOption(emoji=r.partial_emoji(), label=guild.get_role(r.role_id).mention,
                                        value=emoji.emojize(r.emoji)) for r in react_roles]
        self.role_select = self.RfrSelect(max_values=len(options), options=options, row=1)
        self.add_item(self.role_select)

        self.value = None
        self.interaction = None

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey, row=2)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = 0
        self.cancel_button.style = discord.ButtonStyle.green
        self.disable_buttons()
        self.interaction = interaction
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label='Delete Roles', style=discord.ButtonStyle.red, row=2)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = 1
        self.delete_button.style = discord.ButtonStyle.green
        self.disable_buttons()
        self.interaction = interaction
        await interaction.response.edit_message(view=self)
        self.stop()

    def disable_buttons(self):
        self.delete_button.disabled = True
        self.cancel_button.disabled = True
