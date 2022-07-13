#!/usr/bin/env python

"""
Koala Bot Base Code
Run this to start the Bot

Commented using reStructuredText (reST)
"""
__author__ = "KoalaBotUK"
__copyright__ = "Copyright (c) 2020 KoalaBotUK"
__credits__ = ["Jack Draper", "Kieran Allinson", "Viraj Shah", "Stefan Cooper", "Anan Venkatesh", "Harry Nelson",
               "Bill Cao", "Aqeel Little", "Charlie Bowe", "Ponmile Femi-Sunmaila",
               "see full list of developers at: https://koalabot.uk/"]
__license__ = "MIT License"
__version__ = "0.5.8"
__maintainer__ = "Jack Draper, Kieran Allinson, Viraj Shah, Stefan Cooper, Otto Hooper"
__email__ = "koalabotuk@gmail.com"
__status__ = "Development"  # "Prototype", "Development", or "Production"

# Futures
# Built-in/Generic Imports
import asyncio
import time

# Libs
from aiohttp import web
import discord
from discord.ext import commands

# Own modules
from koala.db import extension_enabled
from koala.utils import error_embed
from koala.log import logger
from koala.env import BOT_TOKEN, BOT_OWNER, API_PORT

# Constants
COMMAND_PREFIX = "k!"
OPT_COMMAND_PREFIX = "K!"
STREAMING_URL = "https://twitch.tv/thenuel"
COGS_PACKAGE = "koala.cogs"
TEST_USER = "TestUser#0001"  # Test user for dpytest
TEST_BOT_USER = "FakeApp#0001"  # Test bot user for dpytest
KOALA_GREEN = discord.Colour.from_rgb(0, 170, 110)
PERMISSION_ERROR_TEXT = "This guild does not have this extension enabled, go to http://koalabot.uk, " \
                        "or use `k!help enableExt` to enable it"
KOALA_IMAGE_URL = "https://cdn.discordapp.com/attachments/737280260541907015/752024535985029240/discord1.png"
ENABLED_COGS = ["base", "announce", "colour_role", "intro_cog", "react_for_role", "text_filter", "twitch_alert",
                "verification", "voting"]

# Variables
intent = discord.Intents.default()
intent.members = True
intent.guilds = True
intent.messages = True
bot = commands.Bot(command_prefix=[COMMAND_PREFIX, OPT_COMMAND_PREFIX], intents=intent)
is_dpytest = False


def is_owner(ctx):
    """
    A command used to check if the user of a command is the owner, or the testing bot
    e.g. @commands.check(koalabot.is_owner)
    :param ctx: The context of the message
    :return: True if owner or test, False otherwise
    """
    if is_dm_channel(ctx):
        return False
    elif BOT_OWNER is not None:
        return ctx.author.id == int(BOT_OWNER) or is_dpytest
    else:
        return bot.is_owner(ctx.author) or is_dpytest


def is_admin(ctx):
    """
    A command used to check if the user of a command is the admin, or the testing bot
    e.g. @commands.check(koalabot.is_admin)
    :param ctx: The context of the message
    :return: True if admin or test, False otherwise
    """
    if is_dm_channel(ctx):
        return False
    else:
        return ctx.author.guild_permissions.administrator or is_dpytest


def is_dm_channel(ctx):
    return isinstance(ctx.channel, discord.channel.DMChannel)


def is_guild_channel(ctx):
    return ctx.guild is not None


def load_all_cogs():
    """
    Loads all cogs in ENABLED_COGS into the client
    """

    for cog in ENABLED_COGS:
        try:
            bot.load_extension("."+cog, package=COGS_PACKAGE)
        except commands.errors.ExtensionAlreadyLoaded:
            bot.reload_extension("."+cog, package=COGS_PACKAGE)

    logger.info("All cogs loaded")


def get_channel_from_id(id):
    return bot.get_channel(id=id)


async def dm_group_message(members: [discord.Member], message: str):
    """
    DMs members in a list of members
    :param members: list of members to DM
    :param message: The message to send to the group
    :return: how many were dm'ed successfully.
    """
    count = 0
    for member in members:
        try:
            await member.send(message)
            count = count + 1
        except Exception:  # In case of user dms being closed
            pass
    return count


def check_guild_has_ext(ctx, extension_id):
    """
    A check for if a guild has a given koala extension
    :param ctx: A discord context
    :param extension_id: The koala extension ID
    :return: True if has ext
    """
    if is_dm_channel(ctx):
        return False
    if (not extension_enabled(ctx.message.guild.id, extension_id)) and (not is_dpytest):
        raise PermissionError(PERMISSION_ERROR_TEXT)
    return True


@bot.event
async def on_command_error(ctx, error: Exception):
    if ctx.guild is None:
        guild_id = "UNKNOWN"
        logger.warn("Unknown guild ID threw exception", exc_info=error)
    else:
        guild_id = ctx.guild.id

    if error.__class__ in [commands.MissingRequiredArgument,
                           commands.CommandNotFound]:
        await ctx.send(embed=error_embed(description=error))
    if error.__class__ in [commands.CheckFailure]:
        await ctx.send(embed=error_embed(error_type=str(type(error).__name__),
                                         description=str(error)+"\nPlease ensure you have administrator permissions, "
                                                                "and have enabled this extension."))
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(embed=error_embed(description=f"{ctx.author.mention}, this command is still on cooldown for "
                                                     f"{str(error.retry_after)}s."))
    elif isinstance(error, commands.errors.ChannelNotFound):
        await ctx.send(embed=error_embed(description=f"The channel ID provided is either invalid, or not in this server."))
    elif isinstance(error, commands.CommandInvokeError):
        logger.error("CommandInvokeError(%s), guild_id: %s, message: %s", error.original, guild_id, ctx.message, exc_info=error)
        await ctx.send(embed=error_embed(description=error.original))
    else:
        logger.error(f"Unexpected Error in guild %s : %s", guild_id, error, exc_info=error)
        await ctx.send(embed=error_embed(
            description=f"An unexpected error occurred, please contact an administrator Timestamp: {time.time()}")) # FIXME: better timestamp
        raise error


async def run_bot():
    app = web.Application()

    setattr(bot, "koala_web_app", app)
    load_all_cogs()

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', API_PORT)
    await site.start()

    try:
        await bot.start(BOT_TOKEN)

    except Exception:
        bot.close(),
        raise

    finally:
        await runner.cleanup()

if __name__ == '__main__': # pragma: no cover
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_bot())
