#!/usr/bin/env python

"""
Koala Bot Insights Cog Code
"""
# Futures

# Built-in/Generic Imports

# Libs
from discord.ext import commands

# Own modules
import koalabot
from .log import logger
from .core import get_insights, get_servers

# Constants

# Variables


class Insights(commands.Cog, name="Insights"):
    """
    A discord.py cog with commands to give insight into information about the servers the bot is in
    """

    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="insights")
    @commands.check(koalabot.is_owner)
    async def insights(self, ctx):
        """
        Lists the number of servers the bot is in, and the total number of members across all of those servers
        (includes double counting)
        :param ctx: Context of the command
        """

        await ctx.send(get_insights(self.bot))
        
    @commands.command(name="servers")
    @commands.check(koalabot.is_owner)
    async def list_servers(self, ctx, filter_string=""):
        """
        Lists all servers that the bot is in, optional parameter for specifying that the servers must contain
        a specific string
        :param ctx: Context of the command
        :param filter_string: The string used to filter servers listed
        """

        for message in get_servers(self.bot, filter_string):
            await ctx.send(message)
        

async def setup(bot: koalabot) -> None:
    """
    Loads this cog into the selected bot
    :param bot: The client of the KoalaBot
    """
    await bot.add_cog(Insights(bot))
    logger.info("Insights Cog is ready.")
