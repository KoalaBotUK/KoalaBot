#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import datetime

import discord
from discord.ext import commands, tasks

# Own modules
from sqlalchemy import select

import koalabot
from koala.db import get_all_available_guild_extensions, give_guild_extension, \
    get_enabled_guild_extensions, remove_guild_extension, session_manager
from .utils import new_discord_activity, list_ext_embed
from .log import logger
from .models import ScheduledActivities

# Constants
DEFAULT_ACTIVITY = discord.Activity(type=discord.ActivityType.playing, name=f"{koalabot.COMMAND_PREFIX}help")

# Variables


class BaseCog(commands.Cog, name='KoalaBot'):
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
        self.COGS_DIR = koalabot.COGS_DIR
        self.current_activity = None

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Ran after all cogs have been started and bot is ready
        """
        await self.bot.change_presence(activity=DEFAULT_ACTIVITY)
        self.current_activity = DEFAULT_ACTIVITY
        self.update_activity.start()
        self.started = True
        logger.info("Bot is ready.")

    @commands.group(name="activity")
    @commands.check(koalabot.is_owner)
    async def activity_group(self, ctx: commands.Context):
        """
        Group of commands for activity functionality.
        :param ctx: Context of the command
        :return:
        """

    @activity_group.command(name="set")
    @commands.check(koalabot.is_owner)
    async def activity_set(self, ctx, new_activity, name):
        """
        Change the activity of the bot
        :param ctx: Context of the command
        :param new_activity: The new activity of the bot
        :param name: The name of the activity
        """
        if str.lower(new_activity) in ["playing", "watching", "listening", "streaming"]:
            await self.bot.change_presence(activity=new_discord_activity(new_activity, name))
            await ctx.send(f"I am now {new_activity} {name}")
        else:
            await ctx.send("That is not a valid activity, sorry!\nTry 'playing' or 'watching'")

    @activity_group.command(name="schedule")
    @commands.check(koalabot.is_owner)
    async def activity_schedule(self, ctx, new_activity, message, start_time, end_time, url=None):
        activity_type = discord.ActivityType[str.lower(new_activity)]
        time_start = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
        time_end = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")
        with session_manager() as session:
            activity = ScheduledActivities(activity_type=activity_type, message=message, stream_url=url, time_start=time_start, time_end=time_end)
            session.add(activity)
            session.commit()
            await ctx.send("Activity saved %s" % activity)

    @activity_group.command(name="list")
    @commands.check(koalabot.is_owner)
    async def activity_list(self, ctx, amount=None):
        with session_manager() as session:
            current_time = datetime.datetime.now()
            query = select(ScheduledActivities)

            if not amount or str.lower(amount) != "all":
                query = query.where(ScheduledActivities.time_end > current_time)

            activities = session.execute(query).scalars()
            result = "Activities:"
            for activity in activities:
                result += "\n%s, %s, %s, %s, %s, %s" % (activity.activity_id, activity.activity_type.name,
                                                        activity.stream_url, activity.message, activity.time_start,
                                                        activity.time_end)
            await ctx.send(result)

    @activity_group.command(name="remove")
    @commands.check(koalabot.is_owner)
    async def activity_remove(self, ctx, activity_id):
        with session_manager() as session:
            activity = session.execute(select(ScheduledActivities).filter_by(activity_id=activity_id)).scalar()
            session.delete(activity)
            result = "Removed: "
            result += "\n%s, %s, %s, %s, %s, %s" % (activity.activity_id, activity.activity_type.name,
                                                    activity.stream_url, activity.message, activity.time_start,
                                                    activity.time_end)
            await ctx.send(result)
            session.commit()

    @tasks.loop(seconds=10.0)
    async def update_activity(self):
        with session_manager() as session:
            current_time = datetime.datetime.now()
            query = select(ScheduledActivities).where(ScheduledActivities.time_start < current_time,
                                                      ScheduledActivities.time_end > current_time)
            activity = session.execute(query).scalar()
            if activity:
                new_activity = discord.Activity(
                    type=activity.activity_type, name=activity.message, url=activity.stream_url)
            else:
                new_activity = DEFAULT_ACTIVITY
            if new_activity != self.current_activity:
                await self.bot.change_presence(activity=new_activity)
                logger.info("Auto changing bot presence: %s" % new_activity)
                self.current_activity = new_activity

    @commands.command()
    async def ping(self, ctx):
        """
        Returns the ping of the bot
        :param ctx: Context of the command
        """
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.command()
    async def support(self, ctx):
        """
        KoalaBot Support server link
        :param ctx: Context of the command
        """
        await ctx.send(f"Join our support server for more help! https://discord.gg/5etEjVd")

    @commands.command(name="clear")
    @commands.check(koalabot.is_admin)
    async def clear(self, ctx, amount: int = 1):
        """
        Clears a given number of messages from the given channel
        :param ctx: Context of the command
        :param amount: Amount of lines to delete
        """
        await ctx.channel.purge(limit=amount + 1)

    @commands.command(name="loadCog", aliases=["load_cog"])
    @commands.check(koalabot.is_owner)
    async def load_cog(self, ctx, extension):
        """
        Loads a cog from the cogs folder
        :param ctx: Context of the command
        :param extension: The name of the cog
        """
        self.bot.load_extension(self.COGS_DIR.replace("/", ".") + f'.{extension}')
        await ctx.send(f'{extension} Cog Loaded')

    @commands.command(name="unloadCog", aliases=["unload_cog"])
    @commands.check(koalabot.is_owner)
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

    @commands.command(name="enableExt", aliases=["enable_koala_ext"])
    @commands.check(koalabot.is_admin)
    async def enable_koala_ext(self, ctx, koala_extension):
        """
        Enables a koala extension onto a server, all grants all extensions
        :param ctx: Context of the command
        :param koala_extension: The name of the koala
        """
        guild_id = ctx.message.guild.id

        if koala_extension.lower() in ["all"]:
            available_extensions = get_all_available_guild_extensions(guild_id)
            for extension in available_extensions:
                give_guild_extension(guild_id, extension)
            embed = list_ext_embed(guild_id)
            embed.title = "All extensions enabled"

        else:
            give_guild_extension(guild_id, koala_extension)
            embed = list_ext_embed(guild_id)
            embed.title = koala_extension + " enabled"

        await ctx.send(embed=embed)

    @commands.command(name="disableExt", aliases=["disable_koala_ext"])
    @commands.check(koalabot.is_admin)
    async def disable_koala_ext(self, ctx, koala_extension):
        """
        Disables a koala extension onto a server
        :param ctx: Context of the command
        :param koala_extension: The name of the koala
        """
        guild_id = ctx.message.guild.id
        all_ext = get_enabled_guild_extensions(guild_id)
        if koala_extension.lower() in ["all"]:
            for ext in all_ext:
                remove_guild_extension(guild_id, ext)
        elif koala_extension not in all_ext:
            raise NotImplementedError(f"{koala_extension} is not an enabled extension")
        remove_guild_extension(guild_id, koala_extension)
        embed = list_ext_embed(guild_id)
        embed.title = koala_extension + " disabled"
        await ctx.send(embed=embed)

    @commands.command(name="listExt", aliases=["list_koala_ext"])
    @commands.check(koalabot.is_admin)
    async def list_koala_ext(self, ctx):
        """
        Lists the enabled koala extensions of a server
        :param ctx: Context of the command
        """
        guild_id = ctx.message.guild.id
        embed = list_ext_embed(guild_id)

        await ctx.send(embed=embed)

    @commands.command(name="version")
    @commands.check(koalabot.is_owner)
    async def version(self, ctx):
        """
        Get the version of KoalaBot
        """
        await ctx.send("version: "+koalabot.__version__)


def setup(bot: koalabot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(BaseCog(bot))
    logger.info("BaseCog is ready.")

