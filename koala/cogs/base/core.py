import datetime
from typing import List, Optional

import discord
from discord.ext.commands import Bot
from sqlalchemy import select, exists
from sqlalchemy.orm import Session

import koalabot
from koala.db import assign_session, get_all_available_guild_extensions, get_enabled_guild_extensions, \
    give_guild_extension, remove_guild_extension
from . import db
from .log import logger
from .models import ScheduledActivities
from .utils import DEFAULT_ACTIVITY, activity_eq, list_ext_embed
from ...models import GuildExtensions, Guilds

# Constants

# Variables
current_activity = None


def activity_clear_current():
    global current_activity
    current_activity = None


async def activity_set(activity_type: discord.ActivityType, name: str, url: Optional[str], bot: Bot):
    """
    Set presence for this bot to the given presence
    :param activity_type:
    :param name:
    :param url:
    :param bot: 
    :return:
    """
    new_activity = discord.Activity(type=activity_type, name=name, url=url)
    await bot.change_presence(activity=new_activity)


@assign_session
def activity_schedule(activity_type: discord.ActivityType, message: str, url: Optional[str], start_time: datetime.datetime,
                      end_time: datetime.datetime, **kwargs):
    """
    Schedule an activity to be used for a timed presence
    :param activity_type:
    :param message:
    :param url:
    :param start_time:
    :param end_time:
    :param kwargs:
    :return:
    """
    db.add_scheduled_activity(activity_type, message, url, start_time, end_time, **kwargs)


@assign_session
def activity_list(show_all: bool, **kwargs) -> List[ScheduledActivities]:
    """
    Get a list of all scheduled activity
    :param show_all:
    :param kwargs:
    :return:
    """
    return db.get_scheduled_activities(False, not show_all, **kwargs)


@assign_session
def activity_remove(activity_id: int, **kwargs) -> ScheduledActivities:
    """
    Remove a scheduled activity
    :param activity_id:
    :param kwargs:
    :return:
    """
    return db.remove_scheduled_activities(activity_id, **kwargs)


@assign_session
async def activity_set_current_scheduled(bot: Bot, **kwargs):
    """
    Set the current scheduled activity as the bot presence
    :param bot:
    :param kwargs:
    :return:
    """
    activities = db.get_scheduled_activities(True, True, **kwargs)
    if len(activities) > 1:
        logger.warn("Multiple activities found for this timeslot, %s" % activities)

    if len(activities) != 0:
        activity = activities[0]
        new_activity = discord.Activity(
            type=activity.activity_type, name=activity.message, url=activity.stream_url)
    else:
        new_activity = DEFAULT_ACTIVITY

    global current_activity
    if not activity_eq(new_activity, current_activity):
        await bot.change_presence(activity=new_activity)
        logger.info("Auto changing bot presence: %s" % new_activity)
        current_activity = new_activity


async def ping(bot: Bot):
    """
    Returns the ping of the bot
    :param bot:
    :return:
    """
    return f"Pong! {round(bot.latency * 1000)}ms"


def support_link():
    """
    Returns the link for KoalaBot Support server
    :return:
    """
    return f"Join our support server for more help! https://discord.gg/5etEjVd"


async def purge(bot: Bot, channel_id, amount):
    """
    Purges a number of messages from the channel
    :param channel:
    :param amount:
    :return:
    """
    channel = bot.get_channel(channel_id)
    return await channel.purge(limit=amount+1)


async def load_cog(bot: Bot, extension):
    """
    Loads a cog from the cogs folder
    :param extension:
    :param package:
    :return:
    """
    await bot.load_extension("."+extension, package=koalabot.COGS_PACKAGE)
    return f'{extension} Cog Loaded'


async def unload_cog(bot: Bot, extension):
    """
    Unloads a cog from the cogs folder
    :param extension:
    :param package:
    :return:
    """
    if extension == "base" or extension == "BaseCog":
        raise discord.ext.commands.errors.ExtensionError(message=f"Sorry, you can't unload the base cog", name=extension)
    else:
        await bot.unload_extension("."+extension, package=koalabot.COGS_PACKAGE)
        return f'{extension} Cog Unloaded'


@assign_session
async def enable_extension(bot: Bot, guild_id, koala_extension, **kwargs):
    """
    Enables a koala extension
    :param guild_id:
    :param koala_extension:
    :return:
    """
    if koala_extension.lower() in ["all"]:
        available_extensions = get_all_available_guild_extensions(guild_id, **kwargs)
        for ext in available_extensions:
            give_guild_extension(guild_id, ext, **kwargs)
        
        embed = list_ext_embed(guild_id, **kwargs)
        embed.title = "All extensions enabled"

    else:
        give_guild_extension(guild_id, koala_extension, **kwargs)
        embed = list_ext_embed(guild_id, **kwargs)
        embed.title = koala_extension + " enabled"
    
    return embed


@assign_session
async def disable_extension(bot: Bot, guild_id, koala_extension, *, session: Session):
    """
    Disables a koala extension
    :param guild_id:
    :param koala_extension:
    :return:
    """

    if koala_extension.lower() == "all":
        all_ext = get_enabled_guild_extensions(guild_id, session=session)
        for ext in all_ext:
            remove_guild_extension(guild_id, ext, session=session)
    else:
        enabled_ext = session.execute(select(GuildExtensions)
                                      .filter_by(guild_id=guild_id, extension_id=koala_extension)).scalar()
        if enabled_ext is None:
            raise NotImplementedError(f"{koala_extension} is not an enabled extension")
        koala_extension = enabled_ext.extension_id
        remove_guild_extension(guild_id, koala_extension, session=session)
    embed = list_ext_embed(guild_id, session=session)
    embed.title = koala_extension + " disabled"

    return embed


@assign_session
async def list_enabled_extensions(guild_id, **kwargs):
    """
    Lists enabled koala extensions
    :param guild_id:
    :return:
    """
    embed = list_ext_embed(guild_id, **kwargs)
    return embed


@assign_session
async def get_available_extensions(guild_id, **kwargs):
    """
        Gets all koala extensions of a guild
        :param guild_id:
        :return:
        """
    return get_all_available_guild_extensions(guild_id, **kwargs)


def get_version():
    """
    Returns version of KoalaBot
    :return:
    """
    return "version: "+koalabot.__version__


@assign_session
def add_all_guilds(bot: koalabot.KoalaBot, *, session: Session):
    guilds = bot.guilds
    for guild in guilds:
        db_guild = session.execute(select(Guilds).where(Guilds.guild_id == guild.id)).one_or_none()
        if db_guild is None:
            session.add(Guilds(guild_id=guild.id, subscription=0))
    session.commit()
