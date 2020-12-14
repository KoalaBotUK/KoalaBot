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
        guild_list = self.bot.fetch_guilds()
        guild_list_names = []

        async for guild in guild_list:
            if arg is not None:
                if arg.upper() in guild.name.upper().split(" "):
                    guild_list_names.append(guild.name)
            else:
                guild_list_names.append(guild.name)

        if len(guild_list_names) == 0 and arg is None:
            await ctx.send("KoalaBot is in no servers!")
        elif len(guild_list_names) == 0 and arg is not None:
            await ctx.send(f"No servers with {arg} in their name!")
        else:
            string_to_send = ''
            while len(guild_list_names) != 0:
                length = len(guild_list_names[0])
                if len(string_to_send) + length + 2 > 2000:
                    await ctx.send(string_to_send)
                    string_to_send = ''
                else:
                    guild = guild_list_names.pop(0)
                    string_to_send += guild + ", "
            await ctx.send(string_to_send[:-2])


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Insights(bot))
    print("Insights is ready.")
