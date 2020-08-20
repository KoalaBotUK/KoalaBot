#!/usr/bin/env python

"""
Testing utilities Cog for KoalaBot tests

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
from discord.ext import commands

# Own modules
import KoalaBot


# Constants

# Variables


class TestUtilsCog(commands.Cog):
    """
    A discord cog that can be used when testing
    """

    def __init__(self, bot):
        """
        Initialises the class variables of this cog
        :param bot: The client of the bot being used
        """
        self.bot = bot
        self._last_member = None
        self.last_ctx = None

    @commands.command()
    async def store_ctx(self, ctx):
        """
        Takes the context when this command is used and stores it in this object
        :param ctx: the discord context of the command
        """
        self.last_ctx = ctx

    def get_last_ctx(self):
        """
        A getter for the last ctx got from store_ctx
        :return: last_ctx
        """
        return self.last_ctx


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(TestUtilsCog(bot))
