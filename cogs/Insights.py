#!/usr/bin/env python

"""
Koala Bot Insights Code
Created by: Samuel Tiongson
"""
from discord.ext import commands

import KoalaBot


def insights_is_enabled(ctx):
    """
    A command used to check if the guild has enabled insights
    e.g. @commands.check(KoalaBot.is_admin)
    :param ctx: The context of the message
    :return: True if admin or test, False otherwise
    """
    try:
        result = KoalaBot.check_guild_has_ext(ctx, "Insights")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == KoalaBot.TEST_USER and KoalaBot.is_dpytest)


class Insights(commands.Cog):
    """
    A discord.py cog pertaining to showing the insights of the KoalaBot
    """
    def __init__(self, bot, database_manager=None):
        self.bot = bot

    @commands.check(KoalaBot.is_admin)
    @commands.check(insights_is_enabled)
    @commands.command(name="insightServer", aliases=["insight_server"])
    async def insight_server(self, ctx):
        print("h")









def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Insights(bot))
    print("Insights is ready.")