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


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(RoleColourCog(bot))
