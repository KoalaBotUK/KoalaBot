#!/usr/bin/env python

"""
Koala Bot Base Code
Run this to start the Bot

Commented using reStructuredText (reST)
"""
__author__ = "KoalaBotUK"
__copyright__ = "Copyright (c) 2020 KoalaBotUK"
__credits__ = ["See full list of developers at: https://koalabot.uk/"]
__license__ = "MIT License"
__version__ = "1.0.0"
__maintainer__ = "Jack Draper"
__status__ = "Production"  # "Prototype", "Development", or "Production"

# Futures
# Built-in/Generic Imports
import asyncio
import time
from typing import Any

import aiohttp_cors
import discord
# Libs
from aiohttp import web
from discord.ext import commands

from koala import env
# Own modules
from koala.env import BOT_TOKEN, BOT_OWNER, API_PORT
from koala.errors import KoalaException
from koala.kb2.adapter import kb2_adapter
from koala.kb2.models import Guild, map_ext
from koala.log import logger
from koala.utils import error_embed

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
ENABLED_COGS = ["base", "announce", "colour_role", "insights", "intro_cog", "react_for_role", "text_filter",
                "twitch_alert", "verification", "voting"]

# Variables
intent = discord.Intents.default()
intent.guilds = True        # on_guild_join, on_guild_remove
intent.members = True       # on_member_join
intent.reactions = True     # on_raw_reaction_add
intent.messages = True      # on_message
intent.message_content = True
is_dpytest = False

check_error: [int, str] = {}


class KoalaBot(commands.Bot):
    """
    The commands.Bot subclass for Koala
    """
    def parse_interaction_create(self, data: dict) -> None:
        self.dispatch('raw_interaction', data)

    async def on_raw_interaction(self, raw_interaction: dict):
        await kb2_adapter.on_raw_interaction(raw_interaction)

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        logger.error("Error in %s: %s", event_method, args[0], exc_info=args[0])


    async def on_command_error(self, ctx, error: Exception):
        if ctx.guild is None:
            guild_id = "UNKNOWN"
            logger.warn("Unknown guild ID threw exception", exc_info=error)
        else:
            guild_id = ctx.guild.id

        if error.__class__ in [KoalaException,
                               commands.MissingRequiredArgument,
                               commands.CommandNotFound]:
            await ctx.send(embed=error_embed(description=error))
        if error.__class__ in [commands.CheckFailure]:
            await ctx.send(embed=error_embed(error_type=str(type(error).__name__),
                                             description=str(
                                                 error) + "\nPlease ensure you have administrator permissions, "
                                                          "and have enabled this extension."))
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=error_embed(description=f"{ctx.author.mention}, this command is still on cooldown for "
                                                         f"{str(error.retry_after)}s."))
        elif isinstance(error, commands.errors.ChannelNotFound):
            await ctx.send(
                embed=error_embed(description=f"The channel ID provided is either invalid, or not in this server."))
        elif isinstance(error, commands.CommandInvokeError):
            logger.error("CommandInvokeError(%s), guild_id: %s, message: %s", error.original, guild_id, ctx.message,
                         exc_info=error)
            await ctx.send(embed=error_embed(description=error.original))
        else:
            logger.error(f"Unexpected Error in guild %s : %s", guild_id, error, exc_info=error)
            await ctx.send(embed=error_embed(
                description=f"An unexpected error occurred, please contact an administrator Timestamp: {time.time()}"))  # FIXME: better timestamp
            raise error

    async def setup_hook(self) -> None:
        """
        To perform asynchronous setup after the bot is logged in but before it has connected to the Websocket.
        """
        logger.debug("hook setup started")
        # await self.tree.sync()
        # kb2.main.client.sync_commands()
        # kb2.main.client.sync_commands(guild_ids=[g.id for g in kb2.main.client.guilds])

        self._connection.parsers['INTERACTION_CREATE'] = self.parse_interaction_create

        logger.debug("hook setup complete")

def is_owner(ctx: commands.Context):
    """
    A command used to check if the user of a command is the owner, or the testing bot.
    The command also allows Senior Devs of KoalaBot to use owner only commands (as given by Admin role in the dev portal)
    e.g. @commands.check(koalabot.is_owner)
    :param ctx: The context of the message
    :return: True if owner or test, False otherwise
    """
    if is_dm_channel(ctx):
        return False
    elif BOT_OWNER is not None:
        return ctx.author.id in BOT_OWNER or is_dpytest
    else:
        return ctx.bot.is_owner(ctx.author) or is_dpytest


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


def is_dm_channel(ctx=None, channel=None):
    if ctx is not None:
        channel = ctx.channel
    return isinstance(channel, discord.channel.DMChannel)


def is_guild_channel(ctx):
    return ctx.guild is not None


async def load_all_cogs(bot):
    """
    Loads all cogs in ENABLED_COGS into the client
    """

    for cog in ENABLED_COGS:
        try:
            await bot.load_extension("."+cog, package=COGS_PACKAGE)
        except commands.errors.ExtensionAlreadyLoaded:
            await bot.reload_extension("."+cog, package=COGS_PACKAGE)

    logger.info("All cogs loaded")


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


def check_guild_has_ext(ctx=None, extension_id=None, channel=None, guild_id=None):
    """
    A check for if a guild has a given koala extension
    :param ctx: A discord context
    :param extension_id: The koala extension ID
    :return: True if has ext
    """
    if channel is None and ctx is not None:
        channel = ctx.channel
    if guild_id is None and ctx is not None and ctx.guild is not None:
        guild_id = ctx.guild.id

    if is_dpytest:
        return None
    if is_dm_channel(channel=channel):
        return "DM Channels don't support this command"

    ext = next((e for e in Guild.get(str(guild_id)).extensions
                if e.id == map_ext[extension_id] and e.enabled),
               None)
    if ext is None:
        return "This guild doesn't have this extension enabled"
    else:
        return None


def ext_enabled_func(extension_id):
    return lambda ctx: check_guild_has_ext(ctx, extension_id) is None


def is_kb2(ctx, extension_id):
    if is_dpytest:
        return
    ext = next((e for e in Guild.get(str(ctx.guild.id)).extensions
                if e.id == map_ext[extension_id] and e.enabled),
               None)
    if ext.version == 2:
        raise PermissionError("Please use the new slash commands\n> type `/`")


async def run_bot():
    app = web.Application()

    bot = KoalaBot(command_prefix=[COMMAND_PREFIX, OPT_COMMAND_PREFIX], intents=intent)
    setattr(bot, "koala_web_app", app)
    await load_all_cogs(bot)

    cors = aiohttp_cors.setup(app, defaults={
        env.FRONTEND_URL: aiohttp_cors.ResourceOptions(
                expose_headers="*", allow_headers="*")
    })
    for route in list(app.router.routes()):
        cors.add(route)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', API_PORT)
    await site.start()

    try:
        async with bot:
            await bot.start(BOT_TOKEN)

    except Exception:
        bot.close(),
        raise

    finally:
        await runner.cleanup()

if __name__ == '__main__': # pragma: no cover
    # loop = asyncio.get_event_loop()
    asyncio.run(run_bot())
