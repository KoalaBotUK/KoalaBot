#!/usr/bin/env python

"""
KoalaBot Cog for guild members wishing to change their role colour
"""

# Futures

# Built-in/Generic Imports

# Libs
import discord
from discord.ext import commands

# Own modules
import KoalaBot

# Constants

# Variables


def is_able_to_change_name_colour(ctx):
    """
    A command used to check if the user of a command is the owner, or the testing bot
    e.g. @commands.check(KoalaBot.is_owner)
    :param ctx: The context of the message
    :return: True if allowed to change role colour. False otherwise
    """
    roles_allowed = get_roles_allowed_to_change_colour(ctx.guild.id)
    return


def get_roles_allowed_to_change_colour(guild_id: int):
    """
    Function that returns the list of roles in a guild that are allowed to change their name colour
    :param guild_id: The id of the guild from which this method needed to be called
    :return: The list of roles able to change their name colour in the guild
    """
    return []


class RoleColourCog(commands.Cog):
    """
        A discord.py cog with general commands useful to managers of the bot and servers
    """
    def __init__(self, bot):
        """
        Initialises local variables
        :param bot: The bot client for this cog
        """
        self.bot = bot

    @commands.check(KoalaBot.is_admin)
    @commands.command(name="add_colour_change_role")
    async def add_colour_change_role(self, ctx, role_id: int):
        """
        Adds a role in a guild to the list of allowed roles who can change their name colour
        :param ctx: Context of the command
        :param role_id: Role ID to add to the list
        """
        return

    @commands.check(KoalaBot.is_admin)
    @commands.command(name="remove_colour_change_role")
    async def remove_colour_change_role(self, ctx, role_id: int):
        """
        Removes a role in a guild from the list of allowed roles who can change their name colour
        :param ctx: Context of the command
        :param role_id: Role ID to remove from the list
        """
        return

    @commands.check(KoalaBot.is_admin)
    @commands.command(name="list_allowed_colour_change_roles")
    async def list_allowed_colour_change_roles(self, ctx):
        """
        Sends a message with the list of roles currently allowed to manually choose a custom colour to the channel this command is called in
        :param ctx: Context of the command
        """
        return


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(RoleColourCog(bot))
