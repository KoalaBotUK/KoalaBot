#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
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


def new_discord_activity(activity, name):
    """
    This command takes an activity and name and returns the discord.Activity type for it

    Custom doesn't currently work
    koalabot.uk is added to the end of any activity
    :param activity: The new activity of the bot
    :param name: The name of the activity
    :return: The custom activity created
    """
    name = name + KoalaBot.KOALA_PLUG  # Added to every presence change, do not alter
    lower_activity = str.lower(activity)
    if lower_activity == "playing":
        activity_type = discord.ActivityType.playing
    elif lower_activity == "watching":
        activity_type = discord.ActivityType.watching
    elif lower_activity == "listening":
        activity_type = discord.ActivityType.listening
    elif lower_activity == "streaming":
        return discord.Activity(type=discord.ActivityType.streaming, name=name, url=KoalaBot.STREAMING_URL)
    elif lower_activity == "custom":
        return discord.Activity(type=discord.ActivityType.custom, name=name)
    else:
        raise SyntaxError(f"{activity} is not an activity")
    return discord.Activity(type=activity_type, name=name)


class BaseCog(commands.Cog):
    """
        A discord.py cog with general commands useful to managers of the bot and servers
    """
    def __init__(self, bot):
        """
        Initialises local variables
        :param bot: The bot client for this cog
        """
        self.bot = bot
        self._last_member = None
        self.started = False
        self.COGS_DIR = KoalaBot.COGS_DIR

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Ran after all cogs have been started and bot is ready
        """
        if not self.started:  # Used to prevent changing activity every time the bot connects to discord servers
            await self.bot.change_presence(activity=new_discord_activity("playing", f"{KoalaBot.COMMAND_PREFIX}help"))
            self.started = True
        print("Bot is ready.")

    @commands.command(name="activity", aliases=["change_activity"])
    @commands.check(KoalaBot.is_owner)
    async def change_activity(self, ctx, activity, name):
        """
        Change the activity of the bot
        :param ctx: Context of the command
        :param activity: The new activity of the bot
        :param name: The name of the activity
        """
        if str.lower(activity) in ["playing", "watching", "listening", "streaming"]:
            await self.bot.change_presence(activity=new_discord_activity(activity, name))
            await ctx.send(f"I am now {activity} {name}")
        else:
            await ctx.send("That is not a valid activity, sorry!\nTry 'playing' or 'watching'")

    @commands.command()
    async def ping(self, ctx):
        """
        Returns the ping of the bot
        :param ctx: Context of the command
        """
        await ctx.send(f"Pong! {round(self.bot.latency*1000)}ms")

    @commands.command(name="clear")
    @commands.check(KoalaBot.is_admin)
    async def clear(self, ctx, amount=2):
        """
        Clears a given number of messages from the given channel
        :param ctx: Context of the command
        :param amount: Amount of lines to delete
        """
        await ctx.channel.purge(limit=amount)

    @commands.command(name="loadCog", aliases=["load_cog"])
    @commands.check(KoalaBot.is_owner)
    async def load_cog(self, ctx, extension):
        """
        Loads a cog from the cogs folder
        :param ctx: Context of the command
        :param extension: The name of the cog
        """
        self.bot.load_extension(self.COGS_DIR.replace("/", ".")+f'.{extension}')
        await ctx.send(f'{extension} Cog Loaded')

    @commands.command(name="unloadCog", aliases=["unload_cog"])
    @commands.check(KoalaBot.is_owner)
    async def unload_cog(self, ctx, extension):
        """
        Unloads a running cog
        :param ctx: Context of the command
        :param extension: The name of the cog
        """
        if extension == "BaseCog":
            await ctx.send("Sorry, you can't unload the base cog")
        else:
            self.bot.unload_extension(self.COGS_DIR.replace("/", ".") + f'.{extension}')
            await ctx.send(f'{extension} Cog Unloaded')


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(BaseCog(bot))
