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
__version__ = "0.5.9"
__maintainer__ = "Jack Draper, Kieran Allinson, Viraj Shah, Stefan Cooper, Otto Hooper"
__email__ = "koalabotuk@gmail.com"
__status__ = "Development"  # "Prototype", "Development", or "Production"

# Futures
# Built-in/Generic Imports
import asyncio
import datetime
import sys
import time
from typing import Any

# Libs
from aiohttp import web
import discord
from discord import app_commands
from discord.ext import commands

from koala import checks, env
# Own modules
from koala.db import extension_enabled
from koala.utils import error_embed, interaction_data_to_str
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
intent.guilds = True        # on_guild_join, on_guild_remove
intent.members = True       # on_member_join
intent.reactions = True     # on_raw_reaction_add
intent.messages = True      # on_message
intent.message_content = True
is_dpytest = False


class KoalaBot(commands.Bot):
    """
    The commands.Bot subclass for Koala
    """
    async def setup_hook(self) -> None:
        """
        To perform asynchronous setup after the bot is logged in but before it has connected to the Websocket.
        """
        logger.debug("hook setup")
        await self.tree.sync()
        await self.tree.sync(guild=discord.Object(863362407183286302))
        # todo: sync all guilds, only syncing enabled commands
        #   - add error for rate limiting on server

    async def on_command_error(self, ctx, error: Exception):
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


bot = KoalaBot(command_prefix=[COMMAND_PREFIX, OPT_COMMAND_PREFIX], intents=intent)


@app_commands.guilds(863362407183286302)
class OwnerGroup(app_commands.Group, name='owner', description='owner only commands'):
    # todo: check implementation works across multiple cogs
    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if env.BOT_OWNER is not None:
            success = interaction.user.id == int(env.BOT_OWNER)
        else:
            success = bot.is_owner(interaction.user)
        if not success:
            interaction.data[checks.FAILURE_DESC_ATTR] = "You do not have permission to access this command: not owner"
        return success


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            embed=error_embed(description=f"This command is still on cooldown for {str(error.retry_after)}s."),
            ephemeral=True)
    elif isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(embed=error_embed(interaction.data[checks.FAILURE_DESC_ATTR]))
    else:
        logger.error(f"Unknown error in guild: {interaction.guild_id} for command: "
                     f"`{interaction_data_to_str(interaction.data)}`", exc_info=error)
        await interaction.response.send_message(embed=error_embed(
                    description=f"An unexpected error occurred, "
                                f"please contact an administrator Timestamp: {datetime.datetime.now()}"))


def is_owner(interaction: discord.Interaction):
    """
    A command used to check if the user of a command is the owner, or the testing bot
    e.g. @app_commands.check(koalabot.is_owner)
    :param interaction:
    :return: Whether the user is the owner.
    """
    if BOT_OWNER is not None:
        return interaction.user.id == int(BOT_OWNER) or is_dpytest
    else:
        return bot.is_owner(interaction.user) or is_dpytest


def is_owner_ctx(ctx: commands.Context):
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


def is_dm_channel(ctx):
    return isinstance(ctx.channel, discord.channel.DMChannel)


def is_guild_channel(ctx):
    return ctx.guild is not None


async def load_all_cogs(client):
    """
    Loads all cogs in ENABLED_COGS into the client
    """

    for cog in ENABLED_COGS:
        try:
            await client.load_extension("." + cog, package=COGS_PACKAGE)
        except commands.errors.ExtensionAlreadyLoaded:
            await client.reload_extension("." + cog, package=COGS_PACKAGE)

    logger.info("All cogs loaded")


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


async def run_bot():
    global bot
    app = web.Application()

    setattr(bot, "koala_web_app", app)
    await load_all_cogs(bot)

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


if __name__ == '__main__':  # pragma: no cover
    # loop = asyncio.get_event_loop()
    asyncio.run(run_bot())
