#!/usr/bin/env python

"""
Koala Bot Intro Message Cog Code

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import asyncio

import discord
from discord import app_commands
from discord.ext import commands

# Own modules
import koalabot

from .log import logger
from .ui import EditWelcomeMessage
from .log import logger
from .utils import get_non_bot_members
from . import core
from ...ui import Confirm


# Constants

# Variables

@app_commands.default_permissions(administrator=True)
class IntroCog(commands.GroupCog, group_name="welcome", group_description="Welcome message DMed to users"):
    """
    A discord.py cog with commands pertaining to the welcome messages that a member will receive
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """
        On bot joining guild, add this guild to the database of guild welcome messages.
        :param guild: Guild KoalaBot just joined
        """
        core.new_guild_welcome_message(guild.id)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        On member joining guild, send DM to member with welcome message.
        :param member: Member which just joined guild
        """
        await core.send_member_welcome_message(member)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """
        On bot leaving guild, remove the guild from the database of guild welcome messages
        :param guild: Guild KoalaBot just left
        """
        core.remove_guild_welcome_message(guild.id)

    @app_commands.checks.cooldown(1, 60, key=lambda i: i.guild_id)
    @app_commands.command(name="send", description="Send welcome message to all members")
    async def send_welcome_message(self, interaction: discord.Interaction):
        """
        Allows admins to send out their welcome message manually to all members of a guild. Has a 60 second cooldown per
        guild.

        :param interaction:
        """
        view = Confirm()
        await interaction.response.send_message(
            f"This will DM {len(get_non_bot_members(interaction.guild))} people. Are you sure you wish to do this?",
            view=view, ephemeral=True)
        await view.wait()
        if view.value is None:
            await interaction.edit_original_response(content="Timed out. No message sent.", view=None)
            return False
        elif view.value:
            await core.send_all_members_welcome_messages(interaction.guild)
            await interaction.edit_original_response(content="Okay, sending out the welcome message now.", view=None)
            return True
        else:
            await interaction.edit_original_response(content="Okay, I won't send out the welcome message then.",
                                                     view=None)
            return False

    @app_commands.checks.cooldown(1, 60, key=lambda i: i.guild_id)
    @app_commands.command(name="edit", description="Edit the welcome message")
    async def edit_welcome_message(self, interaction: discord.Interaction):
        """
        Allows admins to change their customisable part of the welcome message of a guild. Has a 60 second cooldown per
        guild.

        :param interaction:
        """
        await interaction.response.send_modal(EditWelcomeMessage(
            core.fetch_guild_welcome_message(interaction.guild_id)))

    @app_commands.command(name="view", description="View your welcome message")
    async def view_welcome_message(self, interaction: discord.Interaction):
        """
        Shows this server's current welcome message
        """
        await interaction.response.send_message(
            f"Your current welcome message is:\n\r{core.get_guild_welcome_message(interaction.guild_id)}")

    @edit_welcome_message.error
    async def on_update_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.MissingRequiredArgument):
            await ctx.send('Please put in a welcome message to update to.')


async def setup(bot: koalabot) -> None:
    """
    Loads this cog into the selected bot
    :param bot: The client of the KoalaBot
    """
    await bot.add_cog(IntroCog(bot))
    logger.info("IntroCog is ready.")
