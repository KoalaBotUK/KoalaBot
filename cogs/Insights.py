#!/usr/bin/env python

"""
Koala Bot Insights Code
Created by: Samuel Tiongson
"""
from discord.ext import commands
import KoalaBot


class Insights(commands.Cog):
    """
    A discord.py cog pertaining to showing the insights of the KoalaBot
    """

    def __init__(self, bot, database_manager=None):
        self.bot = bot

    @commands.check(KoalaBot.is_owner)
    @commands.command(name="insights", aliases=[])
    async def insights(self, ctx):
        """
        Returns the number of servers KoalaBot is in and the total number of members of those servers.

        :param ctx: The discord context
        """
        guilds = self.bot.guilds
        number_of_servers = len(guilds)
        number_of_members = 0

        for guild in guilds:
            number_of_members += guild.member_count

        await ctx.send(f"KoalaBot is in {number_of_servers} servers with a member total of {number_of_members}.")

    @commands.check(KoalaBot.is_owner)
    @commands.command(name="servers", aliases=[])
    async def servers(self, ctx, *, arg=None):
        """
        Returns the names of the servers KoalaBot is in

        :param ctx: The discord context
        :param arg: Searches for guilds with argument provided
        """
        # Retrieves AsyncIterator
        guild_list = self.bot.fetch_guilds()
        guild_list_names = []

        # Cycle through iterator, check if there is an arg, if there is check against the arg, if not just append the
        # guild name
        async for guild in guild_list:
            if arg is not None:
                # Change arg and guild name to uppercase, and split guild name by spaces
                if arg.upper() in guild.name.upper().split(" "):
                    guild_list_names.append(guild.name)
            else:
                guild_list_names.append(guild.name)

        # If there are no guilds and no arguments
        if len(guild_list_names) == 0 and arg is None:
            await ctx.send("KoalaBot is in no servers!")

        # If there are no guilds but there are arguments
        elif len(guild_list_names) == 0 and arg is not None:
            await ctx.send(f"No servers with {arg} in their name!")

        # There must be guilds in the list
        else:
            string_to_send = ''
            # While there are guilds in the list, run code
            while len(guild_list_names) != 0:
                # Get the length of the first server name
                length = len(guild_list_names[0])
                # If this length + the current string length + 2 for comma and space is greater than 2000
                if len(string_to_send) + length + 2 > 2000:
                    # Print the string and reset it to nothing
                    await ctx.send(string_to_send)
                    string_to_send = ''
                else:
                    # If the above is not true, then pop the server name from the list and add it to the string
                    guild = guild_list_names.pop(0)
                    string_to_send += guild + ", "

            # Remove the comma and space at the end of the string
            await ctx.send(string_to_send[:-2])


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Insights(bot))
    print("Insights is ready.")
