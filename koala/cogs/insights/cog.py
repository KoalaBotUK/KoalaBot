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

        message = (f"Insights:\nThis bot is in a total of {len(self.bot.guilds)} servers.\nThere are a total "
                   f"of {sum([len(guild.members) for guild in self.bot.guilds])} members across these servers.")

        await ctx.send(message)
        
    @commands.command(name="servers")
    @commands.check(koalabot.is_owner)
    async def list_servers(self, ctx, filter_string=""):
        """
        Lists all servers that the bot is in, optional parameter for specifying that the servers must contain
        a specific string
        :param ctx: Context of the command
        :param filter_string: The string used to filter servers listed
        """

        if filter_string != "":
            server_list = [guild.name for guild in self.bot.guilds if filter_string.lower() in guild.name.lower()]
        else:
            server_list = [guild.name for guild in self.bot.guilds]
        
        if len(server_list) > 0:
            partial_message = server_list[0]
            for guild in server_list[1:]:
                guild_length = len(guild)
                if len(partial_message) + guild_length + 2 > 2000:
                    await ctx.send(partial_message)
                    partial_message = guild
                else:
                    partial_message += f", {guild}"
            await ctx.send(partial_message)
        else:
            await ctx.send(f"No servers found containing the string \"{filter_string}\".")
        

async def setup(bot: koalabot) -> None:
    """
    Loads this cog into the selected bot
    :param bot: The client of the KoalaBot
    """
    await bot.add_cog(Insights(bot))
    logger.info("Insights Cog is ready.")
